"""Audit routes — create, list, get, status SSE, rerun, delete."""

from __future__ import annotations

import logging
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from app.auth import AuthUser, get_current_user
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

    user = await get_current_user(request)
    supabase = get_supabase_client()

    # Insert audit record
    audit_data = {
        "org_id": user.org_id,
        "created_by": user.id,
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

    logger.info("Audit queued: id=%s url=%s org=%s", audit["id"], payload.url, user.org_id)
    return AuditResponse(**audit)


@router.get("", response_model=list[AuditResponse])
async def list_audits(request: Request) -> list[AuditResponse]:
    """List all audits for the authenticated user's organization."""
    user = await get_current_user(request)
    supabase = get_supabase_client()

    result = (
        supabase.table("audits")
        .select("*")
        .eq("org_id", user.org_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [AuditResponse(**a) for a in result.data]


@router.get("/{audit_id}", response_model=AuditResponse)
async def get_audit(audit_id: UUID, request: Request) -> AuditResponse:
    """Get a single audit with all agent outputs."""
    user = await get_current_user(request)
    supabase = get_supabase_client()

    result = (
        supabase.table("audits")
        .select("*")
        .eq("id", str(audit_id))
        .eq("org_id", user.org_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Audit not found")
    return AuditResponse(**result.data)


@router.get("/{audit_id}/status")
async def audit_status_sse(audit_id: UUID, request: Request) -> EventSourceResponse:
    """SSE endpoint for real-time audit status updates.

    First checks Redis for cached progress state, then falls back to
    polling the database every 2 seconds.
    """
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

            # Try Redis state first for faster updates
            progress_data = _get_redis_progress(str(audit_id))

            if progress_data:
                status = progress_data.get("status", "running")
                progress = int(progress_data.get("progress", 0))
                current_agent = progress_data.get("current_agent")

                if status != last_status or progress != last_progress:
                    if status == "complete":
                        # Fetch final score from DB
                        audit_row = (
                            supabase.table("audits")
                            .select("cro_score, agent_outputs")
                            .eq("id", str(audit_id))
                            .single()
                            .execute()
                        )
                        outputs = audit_row.data.get("agent_outputs", {}) if audit_row.data else {}
                        yield {
                            "event": "audit_complete",
                            "data": json.dumps({
                                "cro_score": audit_row.data.get("cro_score") if audit_row.data else None,
                                "issues_found": len(outputs.get("issues", [])),
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
                        yield {
                            "event": "agent_progress",
                            "data": json.dumps({
                                "agent": current_agent,
                                "progress": progress,
                                "completed_agents": [],
                            }),
                        }

                    last_status = status
                    last_progress = progress
            else:
                # Fallback: poll Supabase directly
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


def _get_redis_progress(audit_id: str) -> dict | None:
    """Read cached audit progress from Redis. Returns None if unavailable."""
    try:
        import redis
        from app.config import get_settings

        settings = get_settings()
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        state = r.hgetall(f"audit:{audit_id}:state")
        return state if state else None
    except Exception:
        return None


@router.post("/{audit_id}/rerun", response_model=AuditResponse)
async def rerun_audit(
    audit_id: UUID,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> AuditResponse:
    """Re-queue an existing audit. Creates a new audit record with previous score."""
    if settings.KILL_AUDIT_QUEUE:
        raise HTTPException(status_code=503, detail="Audit queue is temporarily disabled")

    user = await get_current_user(request)
    supabase = get_supabase_client()

    # Verify audit belongs to this org
    existing = (
        supabase.table("audits")
        .select("*")
        .eq("id", str(audit_id))
        .eq("org_id", user.org_id)
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
    user = await get_current_user(request)
    supabase = get_supabase_client()

    # Verify audit belongs to this org
    existing = (
        supabase.table("audits")
        .select("id")
        .eq("id", str(audit_id))
        .eq("org_id", user.org_id)
        .single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Audit not found")

    # CASCADE will handle issues, reports, etc.
    supabase.table("audits").delete().eq("id", str(audit_id)).execute()
    logger.info("Audit deleted: id=%s", audit_id)
