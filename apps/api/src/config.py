"""
CareerCompiler API settings.
All configuration loaded from environment variables via pydantic-settings.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ─────────────────────────────────────────────────────────────────
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = "change-me-in-production"
    cors_origins: str | list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ── Database ────────────────────────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://ccuser:ccpassword@localhost:5432/careercompiler"
    )

    # ── Redis / Celery ───────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ── LLM ─────────────────────────────────────────────────────────────────
    groq_api_key: str = ""
    groq_model_primary: str = "llama-3.3-70b-versatile"
    groq_model_fast: str = "llama-3.1-8b-instant"

    # ── File Storage ─────────────────────────────────────────────────────────
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    # ── Auth ─────────────────────────────────────────────────────────────────
    dev_auth_bypass: bool = True
    dev_user_id: str = "dev-user-00000000-0000-0000-0000-000000000001"

    # Firebase (Phase 7)
    firebase_project_id: str = ""
    firebase_private_key_id: str = ""
    firebase_private_key: str = ""
    firebase_client_email: str = ""

    # ── Parser ───────────────────────────────────────────────────────────────
    parser_version: str = "1.0.0"
    latex_compiler: str = "tectonic"

    # ── Embeddings ───────────────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_cache_dir: str = "./.cache/sentence_transformers"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
