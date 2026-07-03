"""
Celery Application factory.

Creates and configures the Celery application with Redis as the
broker and result backend. Applies task routing, serialization,
retry policies, and worker concurrency settings from the
application configuration.
"""

import logging
from typing import Any

from celery import Celery

from app.core.config import settings

logger = logging.getLogger(__name__)


def create_celery_app() -> Celery:
    """Create and configure the Celery application.

    Reads connection parameters from ``app.core.config.settings`` and
    applies production-ready defaults for serialization, retries, and
    task execution.

    Returns:
        A fully configured Celery application instance.
    """
    redis_url = settings.redis.redis_url
    broker_url = f"{redis_url}/0"
    result_backend = f"{redis_url}/1"

    logger.info(
        "Creating Celery app: broker=%s result_backend=%s",
        broker_url,
        result_backend,
    )

    app = Celery(
        "ai_research_copilot",
        broker=broker_url,
        backend=result_backend,
    )

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    app.conf.update(
        # Serialization
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        # Timeouts
        task_soft_time_limit=300,
        task_time_limit=600,
        # Retry
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        # Worker
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=100,
        worker_max_memory_per_child=512000,  # 512 MB
        # Result backend
        result_expires=3600,
        result_backend_transport_options={"visibility_timeout": 3600},
        # Task routes
        task_routes={
            "app.tasks.workers.document_worker.*": {"queue": "document_processing"},
            "app.tasks.workers.agent_worker.*": {"queue": "agent_execution"},
            "app.tasks.workers.workflow_worker.*": {"queue": "workflow_execution"},
            "app.tasks.jobs.scheduled_jobs.*": {"queue": "scheduled"},
        },
        # Default queue
        task_default_queue="default",
        # Beat schedule for periodic tasks
        beat_schedule={
            "cleanup-expired-sessions": {
                "task": "app.tasks.jobs.scheduled_jobs.cleanup_expired_sessions",
                "schedule": 3600.0,  # Every hour
            },
            "refresh-knowledge-bases": {
                "task": "app.tasks.jobs.scheduled_jobs.refresh_knowledge_bases",
                "schedule": 86400.0,  # Every 24 hours
            },
        },
    )

    # Auto-discover task modules
    app.autodiscover_tasks(
        [
            "app.tasks.workers",
            "app.tasks.jobs",
        ],
        force=True,
    )

    logger.info("Celery app configured successfully")
    return app
