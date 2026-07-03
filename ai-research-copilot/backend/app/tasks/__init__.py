"""
Celery Tasks package.

Provides the Celery application, background workers, and scheduled
jobs for the AI Research Copilot.
"""

from app.tasks.celery.app import create_celery_app

__all__ = ["create_celery_app"]
