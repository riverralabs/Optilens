"""Optilens FastAPI application entry point."""

from __future__ import annotations

import logging
import re

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

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

# Build CORS origins list — include configured origins + Vercel preview pattern
_cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

# Vercel preview/deployment URLs follow the pattern: *.vercel.app
_VERCEL_ORIGIN_RE = re.compile(r"^https://[a-z0-9\-]+\.vercel\.app$")


def _is_allowed_origin(origin: str) -> bool:
    """Check if origin is in the explicit list or matches Vercel pattern."""
    return origin in _cors_origins or bool(_VERCEL_ORIGIN_RE.match(origin))


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    """CORS middleware that allows configured origins + Vercel preview URLs."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        origin = request.headers.get("origin", "")

        # Handle preflight
        if request.method == "OPTIONS" and origin and _is_allowed_origin(origin):
            response = Response(status_code=200)
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            response.headers["Access-Control-Max-Age"] = "600"
            return response

        response = await call_next(request)

        if origin and _is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


app.add_middleware(DynamicCORSMiddleware)

logger.info("CORS origins: %s (+ *.vercel.app)", _cors_origins)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "optilens-api", "version": "0.1.0", "docs": "/docs"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for Railway / uptime monitors."""
    return {"status": "healthy", "service": "optilens-api"}


# Import and include routers
from app.routers import auth, audits, issues, reports, integrations, workspace, track, github  # noqa: E402

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(audits.router, prefix="/audits", tags=["audits"])
app.include_router(issues.router, prefix="/issues", tags=["issues"])
app.include_router(reports.router, tags=["reports"])
app.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
app.include_router(workspace.router, prefix="/workspace", tags=["workspace"])
app.include_router(track.router, tags=["tracking"])
app.include_router(github.router, tags=["github"])

logger.info("Optilens API started (env=%s)", settings.APP_ENV)
