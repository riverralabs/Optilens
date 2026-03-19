"""Celery worker configuration for Optilens.

Uses Upstash Redis as the message broker.
Start with: celery -A celery_worker.celery_app worker --loglevel=info
"""

from __future__ import annotations

import logging
import ssl

from celery import Celery

from app.config import get_settings

settings = get_settings()

# Upstash requires SSL for rediss:// URLs
_broker_ssl = {"ssl_cert_reqs": ssl.CERT_NONE} if settings.REDIS_URL.startswith("rediss://") else None

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
    # Timeout settings — generous for multi-agent pipeline with crawling + LLM calls
    task_soft_time_limit=600,
    task_time_limit=620,
    # Result expiry
    result_expires=3600,
    # Broker connection retry
    broker_connection_retry_on_startup=True,
    # SSL for Upstash Redis
    broker_use_ssl=_broker_ssl,
    redis_backend_use_ssl=_broker_ssl,
)

logger = logging.getLogger("optilens.celery")
logger.info("Celery worker configured with broker: %s", settings.REDIS_URL[:20] + "...")
