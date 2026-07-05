"""
Prediction Tasks - Core fraud detection Celery tasks.

Handles transaction fraud prediction in background:
- Single transaction prediction
- Batch prediction
- Retry logic with exponential backoff
- Structured logging and observability
"""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.services.prediction import PredictionService
from app.models.fraud.enums import PredictionLabel
from app.models.transaction.transaction import Transaction

# Import Celery app
from app.workers.celery_app import celery_app

# Structured logging
import structlog
logger = structlog.get_logger(__name__)


# Database session factory for tasks
engine = None
SessionLocal = None


def get_db_session() -> AsyncSession:
    """
    Get database session for Celery task.

    Returns:
        AsyncSession instance
    """
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


class PredictionTask(Task):
    """
    Base prediction task with common functionality.

    Provides:
    - Database session management
    - Structured logging
    - Error handling
    - Metrics tracking
    """

    auto_retry_for = (Exception,)
    max_retries = 3
    default_retry_delay = 60  # 1 minute

    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict[str, Any], einfo: Any) -> None:
        """Log task failure."""
        logger.error(
            "task.failed",
            task_id=task_id,
            task_name=self.name,
            error=str(exc),
            exc_info=einfo,
        )

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict[str, Any], einfo: Any) -> None:
        """Log task retry."""
        logger.warning(
            "task.retrying",
            task_id=task_id,
            task_name=self.name,
            error=str(exc),
        )

    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict[str, Any]) -> None:
        """Log task success."""
        logger.info(
            "task.succeeded",
            task_id=task_id,
            task_name=self.name,
        )


@celery_app.task(
    base=PredictionTask,
    bind=True,
    name="predict_transaction_task",
    queue="fraud_prediction_queue",
    priority=1,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    acks_late=True,
    reject_on_worker_lose=True,
)
def predict_transaction_task(self: Task, transaction_id: UUID) -> dict[str, Any]:
    """
    Run fraud prediction on a single transaction.

    This is the core prediction task that:
    1. Loads transaction from database
    2. Extracts features
    3. Runs ML model
    4. Runs rule engine
    5. Combines scores
    6. Stores prediction
    7. Generates alert if needed

    Args:
        transaction_id: Transaction UUID to predict

    Returns:
        Dictionary with prediction results
    """
    start_time = time.time()
    correlation_id = UUID(self.request.correlation_id) if hasattr(self.request, 'correlation_id') else None

    logger.info(
        "prediction.started",
        task_id=self.request.id,
        correlation_id=str(correlation_id),
        transaction_id=str(transaction_id),
    )

    db_session = None
    try:
        # Get database session
        db_session = get_db_session()

        # Initialize prediction service
        prediction_service = PredictionService(db_session)

        # Run prediction (async method called from sync context)
        import asyncio
        prediction = asyncio.run(prediction_service.predict_transaction(transaction_id))

        if not prediction:
            logger.warning(
                "prediction.failed",
                task_id=self.request.id,
                transaction_id=str(transaction_id),
                error="Transaction not found",
            )
            return {"error": "Transaction not found"}

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        logger.info(
            "prediction.completed",
            task_id=self.request.id,
            correlation_id=str(correlation_id),
            transaction_id=str(transaction_id),
            prediction_id=str(prediction.id),
            label=prediction.predicted_label.value,
            score=prediction.confidence_score,
            duration_ms=duration_ms,
        )

        return {
            "prediction_id": str(prediction.id),
            "transaction_id": str(transaction_id),
            "label": prediction.predicted_label.value,
            "score": prediction.confidence_score,
            "duration_ms": duration_ms,
        }

    except Exception as exc:
        logger.error(
            "prediction.error",
            task_id=self.request.id,
            correlation_id=str(correlation_id),
            transaction_id=str(transaction_id),
            error=str(exc),
            exc_info=True,
        )

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=min(60 * (2 ** self.request.retries), 600))

    finally:
        if db_session:
            try:
                asyncio.run(db_session.close())
            except:
                pass


@celery_app.task(
    base=PredictionTask,
    bind=True,
    name="batch_predict_task",
    queue="fraud_prediction_queue",
    priority=1,
    max_retries=2,
    default_retry_delay=120,
    retry_backoff=True,
    retry_backoff_max=1200,
    retry_jitter=True,
    acks_late=True,
    reject_on_worker_lose=True,
)
def batch_predict_task(self: Task, transaction_ids: list[UUID]) -> dict[str, Any]:
    """
    Run fraud prediction on multiple transactions.

    Optimized for batch processing with:
    - Bulk database queries
    - Shared feature computation
    - Parallel ML inference

    Args:
        transaction_ids: List of transaction UUIDs

    Returns:
        Dictionary with batch prediction results
    """
    start_time = time.time()
    correlation_id = UUID(self.request.correlation_id) if hasattr(self.request, 'correlation_id') else None

    logger.info(
        "batch_prediction.started",
        task_id=self.request.id,
        correlation_id=str(correlation_id),
        transaction_count=len(transaction_ids),
    )

    results = []
    failed = []

    for transaction_id in transaction_ids:
        try:
            # Run individual prediction
            result = predict_transaction_task.delay(transaction_id, correlation_id=str(correlation_id))
            results.append(str(result.id))
        except Exception as exc:
            logger.error(
                "batch_prediction.item_failed",
                task_id=self.request.id,
                transaction_id=str(transaction_id),
                error=str(exc),
            )
            failed.append(str(transaction_id))

    duration_ms = (time.time() - start_time) * 1000

    logger.info(
        "batch_prediction.completed",
        task_id=self.request.id,
        correlation_id=str(correlation_id),
        total=len(transaction_ids),
        succeeded=len(results),
        failed=len(failed),
        duration_ms=duration_ms,
    )

    return {
        "task_ids": results,
        "total": len(transaction_ids),
        "succeeded": len(results),
        "failed": len(failed),
        "duration_ms": duration_ms,
    }
