"""
Background Workers Module

Contains Celery application and background task definitions.
"""

from app.workers.celery_app import celery_app

__all__ = ["celery_app"]
