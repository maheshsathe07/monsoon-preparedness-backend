from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter

from app.models.schemas import SupplyItem, SupplyTrackRequest
from app.services.supabase_service import supabase

router = APIRouter(prefix="/supplies", tags=["supplies"])


@router.post("/track", response_model=SupplyItem)
async def track_supply(request: SupplyTrackRequest) -> SupplyItem:
    supply_id = f"supply_{uuid4().hex[:12]}"
    reminder_date = request.expiry_date - timedelta(days=14) if request.expiry_date else None
    payload = {
        "id": supply_id,
        "user_id": request.user_id,
        "item_name": request.item_name,
        "quantity": request.quantity,
        "expiry_date": request.expiry_date,
        "category": request.category,
        "reminder_date": reminder_date,
        "created_at": supabase.now(),
    }
    row = await supabase.insert("supplies", payload)
    return SupplyItem(**row)


@router.get("/upcoming-expiries/{user_id}", response_model=list[SupplyItem])
async def upcoming_expiries(user_id: str) -> list[SupplyItem]:
    rows = await supabase.select("supplies", {"user_id": user_id}, order="expiry_date.asc", limit=100)
    items = [SupplyItem(**row) for row in rows]
    return sorted(items, key=lambda item: item.days_to_expiry if item.days_to_expiry is not None else 99999)
