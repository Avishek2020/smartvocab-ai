"""Application settings. Every value is read from environment variables (see .env.example)."""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "SmartVocab AI"
    environment: Literal["development", "test", "production"] = "development"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    # Comma-separated string. Kept as str on purpose: pydantic-settings would otherwise try to
    # JSON-decode a list field from the environment and crash on "http://a,http://b".
    cors_origins: str = "http://localhost:3000"

    # Database / cache
    database_url: str = "postgresql+psycopg://smartvocab:smartvocab@localhost:5433/smartvocab"
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_secret: str = Field(default="change-me-in-development-only-0123456789", min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24 * 7
    cookie_name: str = "sv_session"
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    # Rate limiting (requests per minute per IP for auth endpoints)
    auth_rate_limit_per_minute: int = 10

    # AI providers (used from Phase 3 onward; documented now so config is stable)
    llm_provider: Literal["anthropic", "openai", "openai_compatible", "none"] = "none"
    llm_model: str = ""
    llm_fast_model: str = ""
    llm_base_url: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    stt_provider: Literal["openai", "faster_whisper", "none"] = "none"
    tts_provider: Literal["azure", "openai", "piper", "none"] = "none"

    # Uploads (Phase 2)
    max_upload_mb: int = 50
    storage_bucket: str = "smartvocab"
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if raw.startswith("["):  # also accept a JSON list
            import json
            return [str(o).strip() for o in json.loads(raw) if str(o).strip()]
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.is_production and s.jwt_secret.startswith("change-me"):
        raise RuntimeError("JWT_SECRET must be set to a strong random value in production")
    return s
