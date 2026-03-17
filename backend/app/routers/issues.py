"""Issue routes — list and update issue status."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.db.supabase import get_supabase_client
from app.models.audit import IssueResponse, IssueUpdate

router = APIRouter()
logger = logging.getLogger("optilens.issues")


@router.patch("/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: UUID,
    payload: IssueUpdate,
    request: Request,
) -> IssueResponse:
    """Update issue status (resolve, dismiss, in_progress)."""
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

    # Verify issue belongs to this org
    existing = (
        supabase.table("issues")
        .select("*")
        .eq("id", str(issue_id))
        .eq("org_id", org_id)
        .single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Issue not found")

    result = (
        supabase.table("issues")
        .update({"status": payload.status})
        .eq("id", str(issue_id))
        .execute()
    )

    logger.info("Issue %s updated to status=%s", issue_id, payload.status)
    return IssueResponse(**result.data[0])
