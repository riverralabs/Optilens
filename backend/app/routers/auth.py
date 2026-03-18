"""Auth routes — user profile and org setup verification.

Note: Actual signup/login is handled by Supabase Auth on the frontend.
The org + user record creation happens directly via the Supabase client
on the frontend during onboarding. This router provides a server-side
endpoint to check if the current user has completed onboarding.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from app.db.supabase import get_supabase_client

router = APIRouter()
logger = logging.getLogger("optilens.auth")


@router.get("/me")
async def get_current_user_profile(request: Request) -> dict:
    """Get the current user's profile and org info.

    Returns the user's role, org_id, and whether onboarding is complete.
    Used by the frontend to determine routing after login.
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
    email = user_response.user.email or ""

    # Check if user has completed onboarding (has a users row with org_id)
    user_row = (
        supabase.table("users")
        .select("org_id, role, email")
        .eq("id", user_id)
        .maybeSingle()
        .execute()
    )

    if not user_row.data:
        return {
            "id": user_id,
            "email": email,
            "onboarding_complete": False,
            "org_id": None,
            "role": None,
        }

    # Get org details
    org = (
        supabase.table("organizations")
        .select("id, name, plan")
        .eq("id", user_row.data["org_id"])
        .single()
        .execute()
    )

    return {
        "id": user_id,
        "email": user_row.data["email"],
        "onboarding_complete": True,
        "org_id": user_row.data["org_id"],
        "role": user_row.data["role"],
        "organization": org.data,
    }
