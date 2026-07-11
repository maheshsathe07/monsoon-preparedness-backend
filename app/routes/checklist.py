from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import ChecklistItem, ChecklistPatchRequest, ChecklistResponse, ChecklistSection
from app.services.supabase_service import supabase

router = APIRouter(prefix="/checklist", tags=["checklist"])


def default_sections(user_id: str) -> ChecklistResponse:
    sections = [
        ChecklistSection(
            section="Home Preparations",
            items=[
                ChecklistItem(id="home_001", title="Move documents and medicines into a waterproof pouch", category="documents", cost_est="Rs 150-300", time_est="20 min", critical=True),
                ChecklistItem(id="home_002", title="Seal low window gaps and inspect balcony drainage", category="structural", cost_est="Rs 300-800", time_est="45 min", critical=True),
                ChecklistItem(id="home_003", title="Charge phones, torch, and power banks before heavy rain alerts", category="power", cost_est="Rs 0", time_est="15 min", critical=True),
            ],
        ),
        ChecklistSection(
            section="Supplies",
            items=[
                ChecklistItem(id="supplies_001", title="Store three days of drinking water per person", category="water", cost_est="Rs 100-400", time_est="30 min", critical=True),
                ChecklistItem(id="supplies_002", title="Pack ready-to-eat food, ORS, sanitizer, and basic medicines", category="food", cost_est="Rs 500-1200", time_est="45 min", critical=True),
            ],
        ),
        ChecklistSection(
            section="Evacuation and Community",
            items=[
                ChecklistItem(id="evac_001", title="Save nearest shelter, hospital, and local emergency numbers offline", category="evacuation", cost_est="Rs 0", time_est="20 min", critical=True),
                ChecklistItem(id="evac_002", title="Share a family meeting point and backup contact with all members", category="family", cost_est="Rs 0", time_est="15 min", critical=True),
            ],
        ),
    ]
    return ChecklistResponse(user_id=user_id, completion_pct=0, sections=sections, last_regenerated_at=datetime.now(timezone.utc))


@router.get("/{user_id}", response_model=ChecklistResponse)
async def get_checklist(user_id: str) -> ChecklistResponse:
    rows = await supabase.select("checklists", {"user_id": user_id}, limit=1)
    if rows:
        row = rows[0]
        return ChecklistResponse(user_id=user_id, completion_pct=row["completion_pct"], sections=row["items"], last_regenerated_at=row["last_regenerated_at"])
    checklist = default_sections(user_id)
    await supabase.upsert(
        "checklists",
        {
            "id": f"checklist_{user_id}",
            "user_id": user_id,
            "items": [section.model_dump() for section in checklist.sections],
            "completion_pct": checklist.completion_pct,
            "last_regenerated_at": checklist.last_regenerated_at,
        },
    )
    return checklist


@router.patch("/{user_id}/{item_id}", response_model=ChecklistResponse)
async def patch_checklist(user_id: str, item_id: str, request: ChecklistPatchRequest) -> ChecklistResponse:
    checklist = await get_checklist(user_id)
    found = False
    total = 0
    done = 0
    for section in checklist.sections:
        for item in section.items:
            total += 1
            if item.id == item_id:
                found = True
                if request.done is not None:
                    item.done = request.done
                if request.notes is not None:
                    item.notes = request.notes
            if item.done:
                done += 1
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist item not found.")
    checklist.completion_pct = round(done * 100 / total) if total else 0
    await supabase.upsert(
        "checklists",
        {
            "id": f"checklist_{user_id}",
            "user_id": user_id,
            "items": [section.model_dump() for section in checklist.sections],
            "completion_pct": checklist.completion_pct,
            "last_regenerated_at": checklist.last_regenerated_at,
        },
    )
    return checklist
