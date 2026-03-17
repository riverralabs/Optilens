"""Re-audit tasks — handle re-running audits with previous score tracking."""

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
def reaudit(self, audit_id: str) -> dict:  # type: ignore[no-untyped-def]
    """Re-run an audit, preserving the previous score for delta tracking."""
    from app.tasks.audit_tasks import run_audit

    logger.info("Re-audit triggered for audit_id=%s", audit_id)
    return run_audit(audit_id)
