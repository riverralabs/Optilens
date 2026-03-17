"""Celery worker configuration for Optilens.

Uses Upstash Redis as the message broker.
Start with: celery -A celery_worker.celery_app worker --loglevel=info
"""

from __future__ import annotations

import logging

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "optilens",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.audit_tasks",
        "app.tasks.reaudit_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Retry settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Timeout settings
    task_soft_time_limit=120,
    task_time_limit=130,
    # Result expiry
    result_expires=3600,
    # Broker connection retry
    broker_connection_retry_on_startup=True,
)

logger = logging.getLogger("optilens.celery")
logger.info("Celery worker configured with broker: %s", settings.REDIS_URL[:20] + "...")
