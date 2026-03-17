"""Optilens FastAPI application entry point."""

from __future__ import annotations

import logging

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

# Validate all environment variables before anything else runs
settings = get_settings()

# Initialize Sentry for error tracking
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.APP_ENV,
    traces_sample_rate=1.0 if settings.APP_ENV == "development" else 0.2,
    profiles_sample_rate=0.1,
)

logger = logging.getLogger("optilens")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Optilens API",
    description="AI-powered CRO audit platform by Riverra Labs LLP",
    version="0.1.0",
)

# CORS — allow configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for Railway / uptime monitors."""
    return {"status": "healthy", "service": "optilens-api"}


# Import and include routers
from app.routers import audits, issues, reports, integrations, workspace, track, github  # noqa: E402

app.include_router(audits.router, prefix="/audits", tags=["audits"])
app.include_router(issues.router, prefix="/issues", tags=["issues"])
app.include_router(reports.router, tags=["reports"])
app.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
app.include_router(workspace.router, prefix="/workspace", tags=["workspace"])
app.include_router(track.router, tags=["tracking"])
app.include_router(github.router, tags=["github"])

logger.info("Optilens API started (env=%s)", settings.APP_ENV)
