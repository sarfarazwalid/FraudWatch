"""
Celery Application Configuration.

Production-grade Celery setup with Redis broker, multiple queues,
retry policies, rate limiting, and structured task routing.
"""

from __future__ import annotations

import os
from typing import Any

from celery import Celery
from kombu import Queue
from celery.signals import task_postrun, task_prerun, worker_ready
import structlog

from app.config.settings import settings

# Configure structured logging
logger = structlog.get_logger(__name__)

# Celery configuration
CELERY_BROKER_URL = settings.redis_url
CELERY_RESULT_BACKEND = settings.redis_url.replace("/0", "/1")

# Task settings
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOSE = True
CELERY_TASK_SEND_SENT_EVENT = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_DISABLE_RATE_LIMITS = False

# Task result settings
CELERY_RESULT_EXPIRES = 3600  # 1 hour
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

# Queue definitions with priorities
CELERY_QUEUES = [
    Queue("fraud_prediction_queue", routing_key="fraud_prediction_queue", queue_arguments={"priority": 1}),
    Queue("alert_generation_queue", routing_key="alert_generation_queue", queue_arguments={"priority": 2}),
    Queue("model_training_queue", routing_key="model_training_queue", queue_arguments={"priority": 3}),
    Queue("analytics_queue", routing_key="analytics_queue", queue_arguments={"priority": 4}),
]

# Default queue
CELERY_TASK_DEFAULT_QUEUE = "fraud_prediction_queue"
CELERY_TASK_DEFAULT_ROUTING_KEY = "fraud_prediction_queue"

# Task routes
CELERY_TASK_ROUTES = {
    # Prediction tasks
    "app.workers.tasks.prediction_tasks.predict_transaction_task": {
        "queue": "fraud_prediction_queue",
        "priority": 1,
        "routing_key": "fraud_prediction_queue",
    },
    "app.workers.tasks.prediction_tasks.batch_predict_task": {
        "queue": "fraud_prediction_queue",
        "priority": 1,
        "routing_key": "fraud_prediction_queue",
    },
    # Alert tasks
    "app.workers.tasks.alert_tasks.generate_fraud_alert_task": {
        "queue": "alert_generation_queue",
        "priority": 2,
        "routing_key": "alert_generation_queue",
    },
    "app.workers.tasks.alert_tasks.escalate_alert_task": {
        "queue": "alert_generation_queue",
        "priority": 2,
        "routing_key": "alert_generation_queue",
    },
    # Model tasks
    "app.workers.tasks.model_tasks.train_model_task": {
        "queue": "model_training_queue",
        "priority": 3,
        "routing_key": "model_training_queue",
    },
    "app.workers.tasks.model_tasks.evaluate_model_task": {
        "queue": "model_training_queue",
        "priority": 3,
        "routing_key": "model_training_queue",
    },
    "app.workers.tasks.model_tasks.deploy_model_task": {
        "queue": "model_training_queue",
        "priority": 3,
        "routing_key": "model_training_queue",
    },
    "app.workers.tasks.model_tasks.rollback_model_task": {
        "queue": "model_training_queue",
        "priority": 3,
        "routing_key": "model_training_queue",
    },
    # Analytics tasks
    "app.workers.tasks.analytics_tasks.update_dashboard_metrics_task": {
        "queue": "analytics_queue",
        "priority": 4,
        "routing_key": "analytics_queue",
    },
    "app.workers.tasks.analytics_tasks.compute_fraud_trends_task": {
        "queue": "analytics_queue",
        "priority": 4,
        "routing_key": "analytics_queue",
    },
    "app.workers.tasks.analytics_tasks.update_risk_statistics_task": {
        "queue": "analytics_queue",
        "priority": 4,
        "routing_key": "analytics_queue",
    },
}

# Retry settings
CELERY_TASK_DEFAULT_RETRY_DELAY = 60  # 1 minute
CELERY_TASK_MAX_RETRIES = 3
CELERY_TASK_RETRY_BACKOFF = True  # Exponential backoff
CELERY_TASK_RETRY_BACKOFF_MAX = 600  # Max 10 minutes
CELERY_TASK_RETRY_JITTER = True  # Add randomness to prevent thundering herd


def create_celery_app() -> Celery:
    """
    Create and configure Celery application.

    Returns:
        Configured Celery instance
    """
    celery_app = Celery(
        "fraudwatch",
        broker=CELERY_BROKER_URL,
        backend=CELERY_RESULT_BACKEND,
        include=[
            "app.workers.tasks.prediction_tasks",
            "app.workers.tasks.alert_tasks",
            "app.workers.tasks.model_tasks",
            "app.workers.tasks.analytics_tasks",
        ],
        task_queues=CELERY_QUEUES,
    )

    # Load configuration
    celery_app.conf.update(
        broker_url=CELERY_BROKER_URL,
        result_backend=CELERY_RESULT_BACKEND,
        task_acks_late=CELERY_TASK_ACKS_LATE,
        task_reject_on_worker_lose=CELERY_TASK_REJECT_ON_WORKER_LOSE,
        task_send_sent_event=CELERY_TASK_SEND_SENT_EVENT,
        worker_prefetch_multiplier=CELERY_WORKER_PREFETCH_MULTIPLIER,
        worker_max_tasks_per_child=CELERY_WORKER_MAX_TASKS_PER_CHILD,
        result_expires=CELERY_RESULT_EXPIRES,
        result_serializer=CELERY_RESULT_SERIALIZER,
        task_serializer=CELERY_TASK_SERIALIZER,
        accept_content=CELERY_ACCEPT_CONTENT,
        task_default_queue=CELERY_TASK_DEFAULT_QUEUE,
        task_default_routing_key=CELERY_TASK_DEFAULT_ROUTING_KEY,
        task_routes=CELERY_TASK_ROUTES,
        task_default_retry_delay=CELERY_TASK_DEFAULT_RETRY_DELAY,
        task_max_retries=CELERY_TASK_MAX_RETRIES,
        task_retry_backoff=CELERY_TASK_RETRY_BACKOFF,
        task_retry_backoff_max=CELERY_TASK_RETRY_BACKOFF_MAX,
        task_retry_jitter=CELERY_TASK_RETRY_JITTER,
        worker_send_task_events=True,
        worker_heartbeat_interval=30,  # 30 seconds
    )

    logger.info("celery_app_configured", broker=CELERY_BROKER_URL)

    return celery_app


# Create Celery app instance
celery_app = create_celery_app()


# Structured logging signals
@task_prerun.connect
def on_task_prerun(task_id: str, task: Any, **kwargs: Any) -> None:
    """Log task start event."""
    logger.info(
        "task.started",
        task_id=task_id,
        task_name=task.name,
        correlation_id=task.request.correlation_id if hasattr(task.request, "correlation_id") else None,
    )


@task_postrun.connect
def on_task_postrun(task_id: str, task: Any, retval: Any, state: str, **kwargs: Any) -> None:
    """Log task completion event."""
    logger.info(
        "task.completed",
        task_id=task_id,
        task_name=task.name,
        state=state,
        duration_ms=task.request.time_limit,  # Approximate
    )


@worker_ready.connect
def on_worker_ready(**kwargs: Any) -> None:
    """Log worker ready event."""
    logger.info("worker.ready", worker=kwargs.get("sender", {}).hostname)
