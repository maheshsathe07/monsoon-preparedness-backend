from uuid import uuid4

from fastapi import APIRouter

from app.core.security import create_access_token, hash_password
from app.models.schemas import AuthResponse, SignupRequest
from app.services.supabase_service import supabase

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest) -> AuthResponse:
    user_id = f"usr_{uuid4().hex[:12]}"
    user = {
        "id": user_id,
        "email": str(request.email) if request.email else None,
        "phone": request.phone,
        "password_hash": hash_password(request.password),
        "location_lat": request.location.lat if request.location else None,
        "location_lng": request.location.lng if request.location else None,
        "prep_level": "minimal",
        "risk_score": 0,
        "created_at": supabase.now(),
    }
    await supabase.insert("users", user)
    return AuthResponse(user_id=user_id, access_token=create_access_token(user_id))
