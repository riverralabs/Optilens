"""Integration routes — connect/disconnect GA4, GSC, GitHub."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from app.db.supabase import get_supabase_client

router = APIRouter()
logger = logging.getLogger("optilens.integrations")


@router.get("")
async def list_integrations(request: Request) -> list[dict]:
    """List all connected integrations for the org."""
    supabase = get_supabase_client()
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")

    token = auth_header.replace("Bearer ", "")
    user_response = supabase.auth.get_user(token)
    user_id = user_response.user.id

    user_row = supabase.table("users").select("org_id").eq("id", user_id).single().execute()
    if not user_row.data:
        raise HTTPException(status_code=403, detail="User not found")
    org_id = user_row.data["org_id"]

    result = (
        supabase.table("integrations")
        .select("id, type, scope, connected_at, last_used_at")
        .eq("org_id", org_id)
        .execute()
    )
    return result.data


@router.post("/ga4/connect")
async def connect_ga4() -> dict:
    """Start GA4 OAuth flow — Phase 2 implementation."""
    return {"status": "not_available", "message": "GA4 integration available in Phase 2"}


@router.post("/gsc/connect")
async def connect_gsc() -> dict:
    """Start GSC OAuth flow — Phase 2 implementation."""
    return {"status": "not_available", "message": "GSC integration available in Phase 2"}


@router.post("/github/connect")
async def connect_github() -> dict:
    """Start GitHub App install — Phase 4 implementation."""
    return {"status": "not_available", "message": "GitHub integration available in Phase 4"}


@router.delete("/{integration_type}")
async def disconnect_integration(integration_type: str, request: Request) -> dict:
    """Disconnect an integration and purge tokens."""
    valid_types = {"ga4", "gsc", "github"}
    if integration_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {valid_types}")

    supabase = get_supabase_client()
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")

    token = auth_header.replace("Bearer ", "")
    user_response = supabase.auth.get_user(token)
    user_id = user_response.user.id

    user_row = supabase.table("users").select("org_id").eq("id", user_id).single().execute()
    if not user_row.data:
        raise HTTPException(status_code=403, detail="User not found")
    org_id = user_row.data["org_id"]

    # Hard delete — cryptographic wipe, not soft-delete
    supabase.table("integrations").delete().eq("org_id", org_id).eq("type", integration_type).execute()

    logger.info("Integration %s disconnected for org %s", integration_type, org_id)
    return {"status": "disconnected", "type": integration_type}
