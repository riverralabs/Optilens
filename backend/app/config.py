"""Application configuration with strict environment variable validation.

All environment variables are validated at startup. If any required variable
is missing, the application refuses to start with a descriptive error.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Optilens application settings. Loaded from environment variables."""

    # --- Anthropic ---
    ANTHROPIC_API_KEY: str

    # --- Supabase ---
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_ANON_KEY: str

    # --- Google OAuth ---
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    # --- GitHub App ---
    GITHUB_APP_ID: str
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_PRIVATE_KEY: str

    # --- Redis (Upstash) ---
    REDIS_URL: str

    # --- Langfuse ---
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # --- Sentry ---
    SENTRY_DSN: str

    # --- Security ---
    ENCRYPTION_KEY: str

    # --- Kill switches (no-redeploy feature flags) ---
    KILL_GITHUB_AGENT: bool = False
    KILL_REVENUE_FIGURES: bool = False
    KILL_AUDIT_QUEUE: bool = False
    KILL_HEATMAP_INGEST: bool = False

    # --- Application ---
    APP_ENV: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    @field_validator("ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """AES-256 requires a 32-byte key (64 hex chars or 44 base64 chars)."""
        if len(v) < 32:
            raise ValueError(
                "ENCRYPTION_KEY must be at least 32 characters for AES-256 encryption"
            )
        return v

    @field_validator("SUPABASE_URL")
    @classmethod
    def validate_supabase_url(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("SUPABASE_URL must start with https://")
        return v

    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        if not (v.startswith("redis://") or v.startswith("rediss://")):
            raise ValueError("REDIS_URL must start with redis:// or rediss://")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Load and cache settings. Fails fast with descriptive error if env vars are missing."""
    try:
        return Settings()  # type: ignore[call-arg]
    except Exception as exc:
        # Surface a clear message identifying which variables are missing
        print(f"\n[FATAL] Environment variable validation failed:\n{exc}\n", file=sys.stderr)
        print(
            "Ensure all required variables are set in .env or the environment.\n"
            "See .env.example for the full list.",
            file=sys.stderr,
        )
        sys.exit(1)
