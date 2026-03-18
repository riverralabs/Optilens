"""Re-audit tasks — create a new audit that references the previous score for delta tracking.

Uses pgvector audit embeddings for re-audit memory so agents can compare
current findings against prior issues.
"""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger("optilens.tasks.reaudit")


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    soft_time_limit=120,
    time_limit=130,
    acks_late=True,
)
def reaudit(self, original_audit_id: str) -> dict:  # type: ignore[no-untyped-def]
    """Re-run an audit, preserving the previous score for delta tracking.

    Creates a new audit record with the previous_score field set from the
    original audit's cro_score, then queues the standard audit pipeline.
    """
    from app.db.supabase import get_supabase_client
    from app.tasks.audit_tasks import run_audit

    supabase = get_supabase_client()

    try:
        # Fetch original audit for context
        original = (
            supabase.table("audits")
            .select("org_id, created_by, url, site_type, cro_score")
            .eq("id", original_audit_id)
            .single()
            .execute()
        )

        if not original.data:
            raise ValueError(f"Original audit {original_audit_id} not found")

        prev_audit = original.data

        # Create new audit record with previous score reference
        new_audit = supabase.table("audits").insert({
            "org_id": prev_audit["org_id"],
            "created_by": prev_audit["created_by"],
            "url": prev_audit["url"],
            "site_type": prev_audit["site_type"],
            "previous_score": prev_audit.get("cro_score"),
            "status": "queued",
        }).execute()

        if not new_audit.data:
            raise ValueError("Failed to create re-audit record")

        new_audit_id = new_audit.data[0]["id"]

        logger.info(
            "Re-audit created: new=%s original=%s previous_score=%s",
            new_audit_id, original_audit_id, prev_audit.get("cro_score"),
        )

        # Run the standard audit pipeline on the new record
        return run_audit(new_audit_id)

    except Exception as exc:
        logger.error(
            "Re-audit failed: original=%s error=%s",
            original_audit_id, str(exc), exc_info=True,
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {"status": "failed", "original_audit_id": original_audit_id, "error": str(exc)}
