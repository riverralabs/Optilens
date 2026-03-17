"""Tracking routes — rrweb event ingest and heatmap data."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import Settings, get_settings
from app.db.supabase import get_supabase_client
from app.models.tracking import EventIngest, HeatmapResponse

router = APIRouter()
logger = logging.getLogger("optilens.tracking")


@router.post("/track", status_code=202)
async def ingest_events(
    payload: EventIngest,
    settings: Settings = Depends(get_settings),
) -> dict:
    """Ingest rrweb events into Supabase."""
    if settings.KILL_HEATMAP_INGEST:
        logger.warning("Heatmap ingest is disabled via KILL_HEATMAP_INGEST")
        return {"status": "skipped", "reason": "Heatmap ingest is temporarily disabled"}

    supabase = get_supabase_client()

    events_data = [
        {
            "org_id": str(payload.org_id),
            "audit_id": str(payload.audit_id) if payload.audit_id else None,
            "page_url": event.page_url,
            "event_type": event.event_type,
            "x": event.x,
            "y": event.y,
            "viewport_w": event.viewport_w,
            "viewport_h": event.viewport_h,
            "session_id": payload.session_id,
        }
        for event in payload.events
    ]

    supabase.table("events").insert(events_data).execute()

    logger.info("Ingested %d events for session %s", len(events_data), payload.session_id)
    return {"status": "accepted", "count": len(events_data)}


@router.get("/heatmap/{audit_id}", response_model=HeatmapResponse)
async def get_heatmap(audit_id: UUID, request: Request) -> HeatmapResponse:
    """Get aggregated heatmap coordinates for h337 rendering."""
    supabase = get_supabase_client()
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")

    result = (
        supabase.table("events")
        .select("x, y, event_type, page_url")
        .eq("audit_id", str(audit_id))
        .execute()
    )

    return HeatmapResponse(
        audit_id=str(audit_id),
        points=[
            {"x": e["x"], "y": e["y"], "value": 1, "event_type": e["event_type"]}
            for e in result.data
            if e.get("x") is not None and e.get("y") is not None
        ],
    )
