from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from app.core.config import get_settings
from app.models.schemas import ActionButton, AlertSummary, ChatResponse, ProfileRequest, ProfileResponse, RecoveryReportResponse


SYSTEM_PROMPT = """You are a practical monsoon preparedness assistant for Indian households.
Return concise, readable JSON only. Avoid markdown tables, decorative symbols, fear-based language, and medical/legal certainty.
Every answer must include user context when available, 2-4 specific next steps, and accessibility-aware guidance for children, elders, disabled people, pets, and low-connectivity situations when relevant."""


def prep_level_for_score(score: int) -> str:
    if score >= 75:
        return "gold"
    if score >= 45:
        return "silver"
    return "bronze"


def _coerce_action_buttons(raw_buttons: Any, fallback_buttons: list[dict[str, str]]) -> list[ActionButton]:
    if not isinstance(raw_buttons, list):
        raw_buttons = fallback_buttons

    buttons: list[ActionButton] = []
    for index, button in enumerate(raw_buttons[:4]):
        if isinstance(button, dict):
            label = str(button.get("label") or button.get("text") or button.get("title") or f"Action {index + 1}")
            endpoint = str(button.get("endpoint") or button.get("url") or button.get("action") or "/chat")
            icon = str(button.get("icon") or "zap")
        else:
            label = str(button)
            lowered = label.lower()
            if "checklist" in lowered:
                endpoint, icon = "/checklist", "list"
            elif "map" in lowered or "shelter" in lowered or "alert" in lowered:
                endpoint, icon = "/alerts", "map"
            elif "id" in lowered or "document" in lowered:
                endpoint, icon = "/emergency-id", "id-card"
            else:
                endpoint, icon = "/chat", "zap"
        buttons.append(ActionButton(label=label[:80], endpoint=endpoint, icon=icon))

    return buttons or [ActionButton(**button) for button in fallback_buttons]


def _coerce_alerts(raw_alerts: Any) -> list[AlertSummary]:
    if not isinstance(raw_alerts, list):
        return []

    alerts: list[AlertSummary] = []
    for alert in raw_alerts[:3]:
        if isinstance(alert, dict):
            alert_type = str(alert.get("type") or "info")
            text = str(alert.get("text") or alert.get("message") or alert.get("title") or "")
        else:
            alert_type = "info"
            text = str(alert)
        if text:
            alerts.append(AlertSummary(type=alert_type, text=text[:240]))
    return alerts


def _coerce_confidence(value: Any, fallback: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return fallback


class OpenAIService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key, timeout=self.settings.openai_timeout_seconds) if self.settings.openai_api_key else None

    async def _json_completion(self, messages: list[dict[str, str]], fallback: dict[str, Any]) -> dict[str, Any]:
        if not self.client:
            return fallback
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except (OpenAIError, json.JSONDecodeError, TimeoutError):
            return fallback

    async def generate_profile(self, request: ProfileRequest, user_id: str) -> ProfileResponse:
        base_score = min(95, 20 + len(request.risks) * 14 + max(0, request.family_size - 2) * 4 + len(request.disabilities) * 8)
        fallback = {
            "risk_score": base_score,
            "recommendation_summary": "Prepare for heavy rainfall with drainage checks, emergency supplies, and a family evacuation plan.",
            "top_mitigations": [
                "Keep documents, medicines, torch, power bank, and drinking water in one waterproof go-bag.",
                "Identify a safe indoor upper-floor area and the nearest shelter or hospital.",
                "Set rainfall alerts and avoid flooded roads during red warnings.",
            ],
        }
        prompt = {
            "family_size": request.family_size,
            "ages": request.age_distribution,
            "disabilities": request.disabilities,
            "location": request.location.model_dump(),
            "risks": request.risks,
            "pets": request.pets,
            "prep_history": request.prep_history,
        }
        data = await self._json_completion(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Calculate monsoon risk as JSON with risk_score integer 0-100, recommendation_summary, and top_mitigations array. Context: {json.dumps(prompt)}"},
            ],
            fallback,
        )
        score = int(data.get("risk_score", base_score))
        score = max(0, min(100, score))
        return ProfileResponse(
            user_id=user_id,
            risk_score=score,
            recommendation_summary=str(data.get("recommendation_summary", fallback["recommendation_summary"])),
            top_mitigations=[str(item) for item in data.get("top_mitigations", fallback["top_mitigations"])[:3]],
            recommended_prep_level=prep_level_for_score(score),
        )

    async def chat(self, message: str, context: dict[str, Any]) -> ChatResponse:
        fallback = {
            "text": "Start with the safest basics: move documents and medicines into waterproof bags, charge phones and power banks, store drinking water, and decide where your household will go if water rises.",
            "action_buttons": [
                {"label": "View Checklist", "endpoint": "/checklist", "icon": "list"},
                {"label": "Check Weather", "endpoint": "/weather", "icon": "cloud-rain"},
                {"label": "Create Emergency ID", "endpoint": "/emergency-id", "icon": "id-card"},
            ],
            "docs_to_link": [],
            "alerts": [],
            "confidence": 0.78,
        }
        data = await self._json_completion(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Answer this monsoon preparedness question as JSON with text, action_buttons, docs_to_link, alerts, confidence. Context: {json.dumps(context)} Question: {message}"},
            ],
            fallback,
        )
        return ChatResponse(
            text=str(data.get("text", fallback["text"])),
            action_buttons=_coerce_action_buttons(data.get("action_buttons"), fallback["action_buttons"]),
            docs_to_link=[str(link) for link in data.get("docs_to_link", [])[:5]] if isinstance(data.get("docs_to_link", []), list) else [],
            alerts=_coerce_alerts(data.get("alerts", [])),
            confidence=_coerce_confidence(data.get("confidence"), fallback["confidence"]),
        )

    async def recovery_report(self, payload: dict[str, Any], report_id: str, pdf_path: str) -> RecoveryReportResponse:
        fallback = {
            "damage_category": "water_damage",
            "severity_level": "moderate",
            "repair_estimate": "Needs professional assessment",
            "incident_summary": payload["damage_description"][:500],
        }
        data = await self._json_completion(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Parse this monsoon damage report as JSON with damage_category, severity_level, repair_estimate, incident_summary: {json.dumps(payload)}"},
            ],
            fallback,
        )
        return RecoveryReportResponse(id=report_id, pdf_path=pdf_path, **{**fallback, **data})


openai_service = OpenAIService()
