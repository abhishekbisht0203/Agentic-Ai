"""
Celery application package.

Re-exports the Celery application factory.
"""

from app.tasks.celery.app import create_celery_app

__all__ = ["create_celery_app"]
