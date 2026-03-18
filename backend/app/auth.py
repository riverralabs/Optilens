"""Authentication dependency for FastAPI routes.

Extracts and validates the Supabase JWT from the Authorization header,
returning the authenticated user's ID and org_id.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import HTTPException, Request

from app.db.supabase import get_supabase_client

logger = logging.getLogger("optilens.auth")


@dataclass
class AuthUser:
    """Authenticated user context available to route handlers."""

    id: str
    org_id: str
    role: str
    email: str


async def get_current_user(request: Request) -> AuthUser:
    """Extract and validate the current user from the Supabase JWT.

    Verifies the token with Supabase Auth, then looks up the user's
    organization and role from the users table.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = auth_header.replace("Bearer ", "")
    supabase = get_supabase_client()

    try:
        user_response = supabase.auth.get_user(token)
    except Exception as exc:
        logger.warning("Token validation failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    if not user_response.user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = user_response.user.id

    # Look up org membership
    user_row = (
        supabase.table("users")
        .select("org_id, role, email")
        .eq("id", user_id)
        .maybeSingle()
        .execute()
    )

    if not user_row.data:
        raise HTTPException(
            status_code=403,
            detail="User account not fully set up. Please complete onboarding.",
        )

    return AuthUser(
        id=user_id,
        org_id=user_row.data["org_id"],
        role=user_row.data["role"],
        email=user_row.data["email"],
    )
