"""Celery tasks for audit execution.

run_audit is the main task that orchestrates the full audit pipeline.
Each agent is called as a subtask with state persisted to Supabase
after each agent completes.
"""

from __future__ import annotations

import logging
import time

from celery import shared_task

logger = logging.getLogger("optilens.tasks")


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

    State machine: queued → running → complete | failed | partial
    Retry policy: 3 attempts with 10s backoff
    Timeout: 120 seconds total
    """
    from app.db.supabase import get_supabase_client

    supabase = get_supabase_client()
    start_time = time.time()

    try:
        # Mark audit as running
        supabase.table("audits").update({"status": "running"}).eq("id", audit_id).execute()
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
        )

        # Calculate duration
        duration = int(time.time() - start_time)

        # Update audit with final results
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

        logger.info("Audit completed: id=%s duration=%ds score=%s", audit_id, duration, final_state.get("cro_score"))
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

        # Update report record
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
