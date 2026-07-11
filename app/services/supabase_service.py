from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings


class SupabaseService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._memory: dict[str, dict[str, dict[str, Any]]] = {
            "users": {},
            "user_profiles": {},
            "checklists": {},
            "emergency_ids": {},
            "alerts": {},
            "supplies": {},
            "chat_history": {},
            "recovery_reports": {},
        }

    @property
    def configured(self) -> bool:
        return bool(self.settings.supabase_url and (self.settings.supabase_service_role_key or self.settings.supabase_key))

    @property
    def _headers(self) -> dict[str, str]:
        key = self.settings.supabase_service_role_key or self.settings.supabase_key or ""
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def _url(self, table: str) -> str:
        return f"{self.settings.supabase_url.rstrip('/')}/rest/v1/{table}"

    async def insert(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        payload = self._json_ready(payload)
        if not self.configured:
            self._memory[table][payload["id"]] = payload
            return payload
        headers = {**self._headers, "Prefer": "return=representation"}
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(self._url(table), headers=headers, json=payload)
        if response.status_code >= 400:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Supabase insert failed for {table}: {response.text}")
        data = response.json()
        return data[0] if data else payload

    async def upsert(self, table: str, payload: dict[str, Any], conflict: str = "id") -> dict[str, Any]:
        payload = self._json_ready(payload)
        if not self.configured:
            self._memory[table][payload["id"]] = payload
            return payload
        headers = {**self._headers, "Prefer": "resolution=merge-duplicates,return=representation"}
        params = {"on_conflict": conflict}
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(self._url(table), headers=headers, params=params, json=payload)
        if response.status_code >= 400:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Supabase upsert failed for {table}: {response.text}")
        data = response.json()
        return data[0] if data else payload

    async def select(
        self,
        table: str,
        filters: dict[str, Any] | None = None,
        order: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        if not self.configured:
            rows = list(self._memory[table].values())
            for field, value in (filters or {}).items():
                rows = [row for row in rows if row.get(field) == value]
            return rows[:limit] if limit else rows
        params: dict[str, str | int] = {"select": "*"}
        for field, value in (filters or {}).items():
            params[field] = f"eq.{value}"
        if order:
            params["order"] = order
        if limit:
            params["limit"] = limit
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(self._url(table), headers=self._headers, params=params)
        if response.status_code >= 400:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Supabase select failed for {table}: {response.text}")
        return response.json()

    async def patch(self, table: str, row_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        payload = self._json_ready(payload)
        if not self.configured:
            existing = self._memory[table].get(row_id, {})
            existing.update(payload)
            self._memory[table][row_id] = existing
            return existing
        headers = {**self._headers, "Prefer": "return=representation"}
        params = {"id": f"eq.{row_id}"}
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.patch(self._url(table), headers=headers, params=params, json=payload)
        if response.status_code >= 400:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Supabase patch failed for {table}: {response.text}")
        data = response.json()
        return data[0] if data else payload

    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _json_ready(self, payload: dict[str, Any]) -> dict[str, Any]:
        def convert(value: Any) -> Any:
            if isinstance(value, (date, datetime)):
                return value.isoformat()
            if hasattr(value, "model_dump"):
                return value.model_dump()
            if isinstance(value, list):
                return [convert(item) for item in value]
            if isinstance(value, dict):
                return {key: convert(item) for key, item in value.items()}
            return value

        return {key: convert(value) for key, value in payload.items()}


supabase = SupabaseService()
