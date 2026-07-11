from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.models.schemas import AuthResponse, LoginRequest, SignupRequest
from app.services.supabase_service import supabase

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest) -> AuthResponse:
    if not request.email and not request.phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or phone is required.")

    existing = []
    if request.email:
        existing = await supabase.select("users", {"email": str(request.email)}, limit=1)
    if not existing and request.phone:
        existing = await supabase.select("users", {"phone": request.phone}, limit=1)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists. Please log in.")

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


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest) -> AuthResponse:
    if not request.email and not request.phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or phone is required.")

    users = []
    if request.email:
        users = await supabase.select("users", {"email": str(request.email)}, limit=1)
    if not users and request.phone:
        users = await supabase.select("users", {"phone": request.phone}, limit=1)
    if not users:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    user = users[0]
    if not verify_password(request.password, user.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    user_id = user["id"]
    return AuthResponse(user_id=user_id, access_token=create_access_token(user_id))
