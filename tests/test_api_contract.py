from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_profile_generates_risk_without_openai() -> None:
    response = client.post(
        "/api/v1/profile",
        json={
            "user_id": "usr_test",
            "family_size": 4,
            "age_distribution": [8, 34, 36, 67],
            "disabilities": ["mobility"],
            "location": {"lat": 19.076, "lng": 72.8777},
            "risks": ["flood", "wind"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["risk_score"] <= 100
    assert body["recommended_prep_level"] in {"bronze", "silver", "gold"}


def test_chat_contract() -> None:
    response = client.post(
        "/api/v1/chat",
        json={
            "user_id": "usr_test",
            "message": "How should I prepare for flooding?",
            "context": {"location": {"lat": 19.076, "lng": 72.8777}, "prep_history": []},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["text"]
    assert isinstance(body["action_buttons"], list)


def test_checklist_patch() -> None:
    response = client.patch("/api/v1/checklist/usr_test/home_001", json={"done": True, "notes": "Packed"})
    assert response.status_code == 200
    body = response.json()
    assert body["completion_pct"] > 0


def test_alert_create_and_list() -> None:
    created = client.post(
        "/api/v1/alerts",
        json={
            "user_id": "usr_test",
            "alert_type": "flood",
            "title": "Waterlogging near station",
            "description": "Knee-level water near the west exit.",
            "location": {"lat": 19.076, "lng": 72.8777},
        },
    )
    assert created.status_code == 200
    listed = client.get("/api/v1/alerts?lat=19.076&lng=72.8777&radius=3")
    assert listed.status_code == 200
    assert listed.json()["alerts"]
