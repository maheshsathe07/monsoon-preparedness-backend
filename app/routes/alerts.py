from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Query

from app.models.schemas import AlertListResponse, CommunityAlert, CommunityAlertCreate
from app.services.supabase_service import supabase
from app.utils.geo import distance_km

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("", response_model=CommunityAlert)
async def create_alert(request: CommunityAlertCreate) -> CommunityAlert:
    alert = CommunityAlert(
        id=f"alert_{uuid4().hex[:12]}",
        user_id=request.user_id,
        type=request.alert_type,
        title=request.title,
        description=request.description,
        location=request.location,
        photo_url=request.photo_url,
        timestamp=datetime.now(timezone.utc),
        confidence=0.82 if request.photo_url else 0.68,
        upvotes=0,
    )
    await supabase.insert(
        "alerts",
        {
            "id": alert.id,
            "user_id": alert.user_id,
            "alert_type": alert.type,
            "location_lat": alert.location.lat,
            "location_lng": alert.location.lng,
            "title": alert.title,
            "description": alert.description,
            "photo_url": alert.photo_url,
            "validation_score": alert.confidence,
            "upvotes": alert.upvotes,
            "created_at": alert.timestamp,
        },
    )
    return alert


@router.get("", response_model=AlertListResponse)
async def list_alerts(lat: float = Query(...), lng: float = Query(...), radius: float = Query(5, gt=0, le=50)) -> AlertListResponse:
    rows = await supabase.select("alerts", order="created_at.desc", limit=100)
    alerts: list[CommunityAlert] = []
    for row in rows:
        dist = distance_km(lat, lng, float(row["location_lat"]), float(row["location_lng"]))
        if dist <= radius:
            alerts.append(
                CommunityAlert(
                    id=row["id"],
                    user_id=row.get("user_id", "demo-user"),
                    type=row["alert_type"],
                    title=row["title"],
                    description=row["description"],
                    location={"lat": row["location_lat"], "lng": row["location_lng"]},
                    photo_url=row.get("photo_url"),
                    timestamp=row.get("created_at") or datetime.now(timezone.utc),
                    distance_km=round(dist, 2),
                    confidence=float(row.get("validation_score") or 0.7),
                    upvotes=int(row.get("upvotes") or 0),
                )
            )
    alerts.sort(key=lambda item: (item.type != "flood", item.distance_km or 999))
    return AlertListResponse(alerts=alerts)
