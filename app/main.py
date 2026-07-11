from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routes import alerts, auth, chat, checklist, emergency_id, profile, reports, supplies, weather

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


for router in [
    auth.router,
    profile.router,
    chat.router,
    checklist.router,
    emergency_id.router,
    weather.router,
    alerts.router,
    supplies.router,
    reports.router,
]:
    app.include_router(router, prefix=settings.api_v1_prefix)
