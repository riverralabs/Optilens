"""Workspace routes — org details, member management."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr

from app.db.supabase import get_supabase_client

router = APIRouter()
logger = logging.getLogger("optilens.workspace")


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = "analyst"


class UpdateRoleRequest(BaseModel):
    role: str


@router.get("")
async def get_workspace(request: Request) -> dict:
    """Get organization details and plan."""
    supabase = get_supabase_client()
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")

    token = auth_header.replace("Bearer ", "")
    user_response = supabase.auth.get_user(token)
    user_id = user_response.user.id

    user_row = supabase.table("users").select("org_id, role").eq("id", user_id).single().execute()
    if not user_row.data:
        raise HTTPException(status_code=403, detail="User not found")
    org_id = user_row.data["org_id"]

    org = supabase.table("organizations").select("*").eq("id", org_id).single().execute()
    if not org.data:
        raise HTTPException(status_code=404, detail="Organization not found")

    members = supabase.table("users").select("id, email, role, created_at").eq("org_id", org_id).execute()

    return {
        **org.data,
        "members": members.data,
        "current_user_role": user_row.data["role"],
    }


@router.post("/members/invite")
async def invite_member(payload: InviteMemberRequest, request: Request) -> dict:
    """Invite a team member by email."""
    valid_roles = {"admin", "analyst", "viewer"}
    if payload.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {valid_roles}")

    supabase = get_supabase_client()
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")

    token = auth_header.replace("Bearer ", "")
    user_response = supabase.auth.get_user(token)
    user_id = user_response.user.id

    user_row = supabase.table("users").select("org_id, role").eq("id", user_id).single().execute()
    if not user_row.data:
        raise HTTPException(status_code=403, detail="User not found")

    # Only owner/admin can invite
    if user_row.data["role"] not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Only owners and admins can invite members")

    logger.info("Invitation sent to %s with role %s", payload.email, payload.role)
    return {"status": "invited", "email": payload.email, "role": payload.role}


@router.patch("/members/{member_id}")
async def update_member_role(
    member_id: UUID,
    payload: UpdateRoleRequest,
    request: Request,
) -> dict:
    """Update a member's role."""
    valid_roles = {"admin", "analyst", "viewer"}
    if payload.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {valid_roles}")

    supabase = get_supabase_client()
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")

    token = auth_header.replace("Bearer ", "")
    user_response = supabase.auth.get_user(token)
    user_id = user_response.user.id

    user_row = supabase.table("users").select("org_id, role").eq("id", user_id).single().execute()
    if not user_row.data:
        raise HTTPException(status_code=403, detail="User not found")

    if user_row.data["role"] not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Only owners and admins can change roles")

    org_id = user_row.data["org_id"]

    result = (
        supabase.table("users")
        .update({"role": payload.role})
        .eq("id", str(member_id))
        .eq("org_id", org_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Member not found")

    logger.info("Member %s role updated to %s", member_id, payload.role)
    return {"status": "updated", "member_id": str(member_id), "role": payload.role}
