"""Celery tasks for audit execution.

run_audit is the main task that orchestrates the full audit pipeline.
Each agent is called as a subtask with state persisted to Supabase
after each agent completes. Progress is published to Redis for SSE.
"""

from __future__ import annotations

import json
import logging
import time

from celery import shared_task

logger = logging.getLogger("optilens.tasks")

# Agent stages in pipeline order — used for progress calculation
AGENT_STAGES = [
    "site_intelligence",
    "ux_vision",
    "copy_content",
    "data_performance",
    "synthesis",
]


def _publish_progress(audit_id: str, agent: str, status: str, progress: int) -> None:
    """Publish audit progress to Redis for SSE consumers.

    Writes both a pub/sub message (for real-time listeners) and a
    hash key (for late-joining clients).
    """
    try:
        import redis
        from app.config import get_settings

        settings = get_settings()
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)

        payload = json.dumps({
            "audit_id": audit_id,
            "agent": agent,
            "status": status,
            "progress": progress,
            "completed_agents": [],
            "timestamp": time.time(),
        })

        # Pub/sub for real-time SSE listeners
        r.publish(f"audit:{audit_id}:progress", payload)

        # Hash for late-joining clients — expires in 1 hour
        r.hset(f"audit:{audit_id}:state", mapping={
            "current_agent": agent,
            "status": status,
            "progress": str(progress),
            "updated_at": str(time.time()),
        })
        r.expire(f"audit:{audit_id}:state", 3600)
    except Exception as exc:
        # Progress publishing is best-effort — don't crash the audit
        logger.warning("Failed to publish progress for audit %s: %s", audit_id, exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    soft_time_limit=120,
    time_limit=130,
    acks_late=True,
)
def run_audit(self, audit_id: str) -> dict:  # type: ignore[no-untyped-def]
    """Main audit task — runs the full LangGraph agent pipeline.

    State machine: queued -> running -> complete | failed | partial
    Retry policy: 3 attempts with 10s backoff
    Timeout: 120 seconds total, 45 seconds per agent
    """
    from app.db.supabase import get_supabase_client

    supabase = get_supabase_client()
    start_time = time.time()

    try:
        # Mark audit as running
        supabase.table("audits").update({"status": "running"}).eq("id", audit_id).execute()
        _publish_progress(audit_id, "initializing", "running", 0)
        logger.info("Audit started: id=%s", audit_id)

        # Fetch audit details
        audit_result = supabase.table("audits").select("*").eq("id", audit_id).single().execute()
        if not audit_result.data:
            raise ValueError(f"Audit {audit_id} not found")

        audit = audit_result.data

        # Run the LangGraph pipeline (implemented in Step 1.6)
        from app.agents.orchestrator import run_audit_pipeline

        final_state = run_audit_pipeline(
            audit_id=audit_id,
            org_id=audit["org_id"],
            url=audit["url"],
            progress_callback=_publish_progress,
        )

        # Calculate duration
        duration = int(time.time() - start_time)

        # Persist final results to Supabase
        supabase.table("audits").update({
            "status": "complete",
            "cro_score": final_state.get("cro_score"),
            "site_type": final_state.get("site_type"),
            "framework_applied": final_state.get("framework"),
            "revenue_leak_monthly": final_state.get("revenue_leak_monthly"),
            "revenue_leak_confidence": final_state.get("revenue_leak_confidence", "Estimated"),
            "agent_outputs": final_state.get("agent_outputs", {}),
            "audit_duration_seconds": duration,
            "completed_at": "now()",
        }).eq("id", audit_id).execute()

        _publish_progress(audit_id, "complete", "complete", 100)
        logger.info(
            "Audit completed: id=%s duration=%ds score=%s",
            audit_id, duration, final_state.get("cro_score"),
        )
        return {"status": "complete", "audit_id": audit_id, "duration": duration}

    except Exception as exc:
        duration = int(time.time() - start_time)
        logger.error("Audit failed: id=%s error=%s", audit_id, str(exc), exc_info=True)

        # Mark as failed with error details
        supabase.table("audits").update({
            "status": "failed",
            "agent_outputs": {"error": str(exc)},
            "audit_duration_seconds": duration,
        }).eq("id", audit_id).execute()

        _publish_progress(audit_id, "failed", "failed", 0)

        # Retry if attempts remain
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

        return {"status": "failed", "audit_id": audit_id, "error": str(exc)}


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=5,
    soft_time_limit=60,
    time_limit=70,
)
def generate_report_task(self, audit_id: str) -> dict:  # type: ignore[no-untyped-def]
    """Regenerate report (PDF + Excel) for a completed audit."""
    from app.db.supabase import get_supabase_client

    supabase = get_supabase_client()

    try:
        audit_result = supabase.table("audits").select("*").eq("id", audit_id).single().execute()
        if not audit_result.data:
            raise ValueError(f"Audit {audit_id} not found")

        audit = audit_result.data
        if audit["status"] != "complete":
            raise ValueError(f"Audit {audit_id} is not complete (status={audit['status']})")

        # Generate PDF (implemented in Step 1.8)
        from app.services.pdf import generate_audit_pdf

        pdf_path = generate_audit_pdf(audit)

        # Upsert report record
        org_id = audit["org_id"]
        supabase.table("reports").upsert({
            "audit_id": audit_id,
            "org_id": org_id,
            "pdf_url": pdf_path,
        }).execute()

        logger.info("Report regenerated for audit %s", audit_id)
        return {"status": "complete", "audit_id": audit_id}

    except Exception as exc:
        logger.error("Report generation failed: audit=%s error=%s", audit_id, str(exc), exc_info=True)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {"status": "failed", "audit_id": audit_id, "error": str(exc)}
