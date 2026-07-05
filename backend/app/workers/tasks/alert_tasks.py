"""
Alert Tasks - Fraud alert generation and management.

Handles:
- Fraud alert generation from predictions
- Alert escalation
- Alert notification routing
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.workers.celery_app import celery_app

import structlog
logger = structlog.get_logger(__name__)

# Database session factory
engine = None
SessionLocal = None


def get_db_session() -> AsyncSession:
    """Get database session for Celery task."""
    global engine, SessionLocal

    if engine is None:
        engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
        )
        SessionLocal = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

    return SessionLocal()


class AlertTask(Task):
    """Base alert task with common functionality."""

    auto_retry_for = (Exception,)
    max_retries = 3
    default_retry_delay = 30

    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict[str, Any], einfo: Any) -> None:
        logger.error(
            "task.failed",
            task_id=task_id,
            task_name=self.name,
            error=str(exc),
            exc_info=einfo,
        )

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict[str, Any], einfo: Any) -> None:
        logger.warning(
            "task.retrying",
            task_id=task_id,
            task_name=self.name,
            error=str(exc),
        )

    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict[str, Any]) -> None:
        logger.info(
            "task.succeeded",
            task_id=task_id,
            task_name=self.name,
        )


@celery_app.task(
    base=AlertTask,
    bind=True,
    name="generate_fraud_alert_task",
    queue="alert_generation_queue",
    priority=2,
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    acks_late=True,
    reject_on_worker_lose=True,
)
def generate_fraud_alert_task(self: Task, prediction_id: UUID) -> dict[str, Any]:
    """
    Generate fraud alert from prediction.

    Args:
        prediction_id: Prediction UUID

    Returns:
        Alert generation result
    """
    logger.info(
        "alert_generation.started",
        task_id=self.request.id,
        prediction_id=str(prediction_id),
    )

    db_session = None
    try:
        db_session = get_db_session()

        # Placeholder for alert generation logic
        # In production: create FraudAlert record, send notifications

        logger.info(
            "alert_generation.completed",
            task_id=self.request.id,
            prediction_id=str(prediction_id),
        )

        return {
            "prediction_id": str(prediction_id),
            "alert_id": None,
        }

    except Exception as exc:
        logger.error(
            "alert_generation.error",
            task_id=self.request.id,
            prediction_id=str(prediction_id),
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=min(30 * (2 ** self.request.retries), 300))

    finally:
        if db_session:
            try:
                import asyncio
                asyncio.run(db_session.close())
            except:
                pass


@celery_app.task(
    base=AlertTask,
    bind=True,
    name="escalate_alert_task",
    queue="alert_generation_queue",
    priority=2,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    acks_late=True,
    reject_on_worker_lose=True,
)
def escalate_alert_task(self: Task, alert_id: UUID) -> dict[str, Any]:
    """
    Escalate fraud alert to next level.

    Args:
        alert_id: Alert UUID

    Returns:
        Escalation result
    """
    logger.info(
        "alert.escalation.started",
        task_id=self.request.id,
        alert_id=str(alert_id),
    )

    db_session = None
    try:
        db_session = get_db_session()

        # Placeholder for escalation logic

        logger.info(
            "alert.escalation.completed",
            task_id=self.request.id,
            alert_id=str(alert_id),
        )

        return {
            "alert_id": str(alert_id),
            "escalated": True,
        }

    except Exception as exc:
        logger.error(
            "alert.escalation.error",
            task_id=self.request.id,
            alert_id=str(alert_id),
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=min(60 * (2 ** self.request.retries), 600))

    finally:
        if db_session:
            try:
                import asyncio
                asyncio.run(db_session.close())
            except:
                pass
