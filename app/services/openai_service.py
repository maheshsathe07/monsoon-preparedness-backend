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
            action_buttons=[ActionButton(**button) for button in data.get("action_buttons", fallback["action_buttons"])[:4]],
            docs_to_link=[str(link) for link in data.get("docs_to_link", [])[:5]],
            alerts=[AlertSummary(**alert) for alert in data.get("alerts", [])[:3]],
            confidence=float(data.get("confidence", fallback["confidence"])),
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
