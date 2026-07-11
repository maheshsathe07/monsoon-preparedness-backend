import json
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


REQUIRED_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "https://monsoon-preparedness-app-s6kv.vercel.app",
]


class Settings(BaseSettings):
    app_name: str = "Monsoon Preparedness API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: str = ",".join(REQUIRED_CORS_ORIGINS)

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: int = 20

    supabase_url: str | None = None
    supabase_key: str | None = None
    supabase_service_role_key: str | None = None

    jwt_secret: str = Field(default="dev-only-change-me")
    jwt_expire_hours: int = 48
    rate_limit_per_minute: int = 50
    data_dir: Path = Path("storage")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        raw = self.backend_cors_origins.strip()
        configured: list[str]
        if raw.startswith("["):
            try:
                origins = json.loads(raw)
                configured = [str(origin).strip().rstrip("/") for origin in origins if str(origin).strip()]
            except json.JSONDecodeError:
                configured = []
        else:
            configured = [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]

        merged = [*configured, *REQUIRED_CORS_ORIGINS]
        return list(dict.fromkeys(origin.rstrip("/") for origin in merged))


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
