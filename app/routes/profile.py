from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import ProfileRequest, ProfileResponse
from app.services.openai_service import openai_service
from app.services.supabase_service import supabase
from app.utils.geo import validate_monsoon_region

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("", response_model=ProfileResponse)
async def create_profile(request: ProfileRequest) -> ProfileResponse:
    if not validate_monsoon_region(request.location.lat, request.location.lng):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location appears outside the supported Indian monsoon region.")
    user_id = request.user_id or f"usr_{uuid4().hex[:12]}"
    result = await openai_service.generate_profile(request, user_id)
    await supabase.upsert(
        "user_profiles",
        {
            "id": f"profile_{user_id}",
            "user_id": user_id,
            "family_size": request.family_size,
            "ages": request.age_distribution,
            "disabilities": request.disabilities,
            "risks": request.risks,
            "pets": request.pets,
            "location_lat": request.location.lat,
            "location_lng": request.location.lng,
            "updated_at": supabase.now(),
        },
    )
    await supabase.patch("users", user_id, {"risk_score": result.risk_score, "prep_level": result.recommended_prep_level})
    return result
