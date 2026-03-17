"""Audit routes — create, list, get, status SSE, rerun, delete."""

from __future__ import annotations

import logging
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from app.config import Settings, get_settings
from app.db.supabase import get_supabase_client
from app.models.audit import AuditCreate, AuditResponse, AuditStatusEvent

router = APIRouter()
logger = logging.getLogger("optilens.audits")


@router.post("", response_model=AuditResponse, status_code=201)
async def create_audit(
    payload: AuditCreate,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> AuditResponse:
    """Create a new audit and queue it via Celery."""
    if settings.KILL_AUDIT_QUEUE:
        logger.warning("Audit queue is disabled via KILL_AUDIT_QUEUE")
        raise HTTPException(status_code=503, detail="Audit queue is temporarily disabled")

    supabase = get_supabase_client()

    # Get user from auth header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")

    token = auth_header.replace("Bearer ", "")
    user_response = supabase.auth.get_user(token)
    user_id = user_response.user.id

    # Resolve org_id from users table
    user_row = supabase.table("users").select("org_id").eq("id", user_id).single().execute()
    if not user_row.data:
        raise HTTPException(status_code=403, detail="User not found")
    org_id = user_row.data["org_id"]

    # Insert audit record
    audit_data = {
        "org_id": org_id,
        "created_by": user_id,
        "url": str(payload.url),
        "status": "queued",
    }
    result = supabase.table("audits").insert(audit_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create audit")

    audit = result.data[0]

    # Queue Celery task
    from app.tasks.audit_tasks import run_audit
    run_audit.delay(audit["id"])

    logger.info("Audit queued: id=%s url=%s org=%s", audit["id"], payload.url, org_id)
    return AuditResponse(**audit)


@router.get("", response_model=list[AuditResponse])
async def list_audits(request: Request) -> list[AuditResponse]:
    """List all audits for the authenticated user's organization."""
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
        supabase.table("audits")
        .select("*")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [AuditResponse(**a) for a in result.data]


@router.get("/{audit_id}", response_model=AuditResponse)
async def get_audit(audit_id: UUID, request: Request) -> AuditResponse:
    """Get a single audit with all agent outputs."""
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
        supabase.table("audits")
        .select("*")
        .eq("id", str(audit_id))
        .eq("org_id", org_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Audit not found")
    return AuditResponse(**result.data)


@router.get("/{audit_id}/status")
async def audit_status_sse(audit_id: UUID, request: Request) -> EventSourceResponse:
    """SSE endpoint for real-time audit status updates."""
    import asyncio
    import json

    supabase = get_supabase_client()

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        """Yield SSE events as audit progresses."""
        last_status = None
        last_progress = -1

        while True:
            if await request.is_disconnected():
                break

            result = (
                supabase.table("audits")
                .select("status, agent_outputs, cro_score")
                .eq("id", str(audit_id))
                .single()
                .execute()
            )

            if not result.data:
                yield {"event": "error", "data": json.dumps({"message": "Audit not found"})}
                break

            audit = result.data
            status = audit["status"]
            agent_outputs = audit.get("agent_outputs") or {}

            # Calculate progress from completed agents
            agents = ["site_intelligence", "ux_vision", "copy_content", "data_performance"]
            completed = sum(1 for a in agents if a in agent_outputs)
            progress = int((completed / len(agents)) * 100)

            if status != last_status or progress != last_progress:
                if status == "complete":
                    yield {
                        "event": "audit_complete",
                        "data": json.dumps({
                            "cro_score": audit.get("cro_score"),
                            "issues_found": len(agent_outputs.get("issues", [])),
                            "report_ready": True,
                        }),
                    }
                    break
                elif status == "failed":
                    yield {
                        "event": "audit_failed",
                        "data": json.dumps({"message": "Audit failed"}),
                    }
                    break
                else:
                    # Find currently running agent
                    current_agent = agents[completed] if completed < len(agents) else None
                    yield {
                        "event": "agent_progress",
                        "data": json.dumps({
                            "agent": current_agent,
                            "progress": progress,
                            "completed_agents": [a for a in agents if a in agent_outputs],
                        }),
                    }

                last_status = status
                last_progress = progress

            await asyncio.sleep(2)

    return EventSourceResponse(event_generator())


@router.post("/{audit_id}/rerun", response_model=AuditResponse)
async def rerun_audit(
    audit_id: UUID,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> AuditResponse:
    """Re-queue an existing audit."""
    if settings.KILL_AUDIT_QUEUE:
        raise HTTPException(status_code=503, detail="Audit queue is temporarily disabled")

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

    # Verify audit belongs to this org
    existing = (
        supabase.table("audits")
        .select("*")
        .eq("id", str(audit_id))
        .eq("org_id", org_id)
        .single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Audit not found")

    # Store previous score for delta calculation
    previous_score = existing.data.get("cro_score")

    # Reset audit state
    update_data = {
        "status": "queued",
        "cro_score": None,
        "previous_score": previous_score,
        "agent_outputs": {},
        "completed_at": None,
        "audit_duration_seconds": None,
    }
    result = (
        supabase.table("audits")
        .update(update_data)
        .eq("id", str(audit_id))
        .execute()
    )

    from app.tasks.audit_tasks import run_audit
    run_audit.delay(str(audit_id))

    logger.info("Audit re-queued: id=%s", audit_id)
    return AuditResponse(**result.data[0])


@router.delete("/{audit_id}", status_code=204)
async def delete_audit(audit_id: UUID, request: Request) -> None:
    """Delete an audit and all associated assets."""
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

    # Verify audit belongs to this org
    existing = (
        supabase.table("audits")
        .select("id")
        .eq("id", str(audit_id))
        .eq("org_id", org_id)
        .single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Audit not found")

    # CASCADE will handle issues, reports, etc.
    supabase.table("audits").delete().eq("id", str(audit_id)).execute()
    logger.info("Audit deleted: id=%s", audit_id)
