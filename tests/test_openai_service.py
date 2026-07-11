import pytest

from app.services.openai_service import OpenAIService


@pytest.mark.asyncio
async def test_chat_accepts_string_action_buttons(monkeypatch):
    service = OpenAIService()

    async def fake_completion(messages, fallback):
        return {
            "text": "Keep documents dry and check the forecast.",
            "action_buttons": ["Open checklist", "Find shelters on map"],
            "alerts": ["Heavy rain may affect low-lying roads"],
            "confidence": "0.91",
        }

    monkeypatch.setattr(service, "_json_completion", fake_completion)

    response = await service.chat("How do I prepare?", {"location": {"lat": 19.076, "lng": 72.8777}})

    assert response.action_buttons[0].label == "Open checklist"
    assert response.action_buttons[0].endpoint == "/checklist"
    assert response.action_buttons[1].endpoint == "/alerts"
    assert response.alerts[0].type == "info"
    assert response.confidence == 0.91
