"""
Model Tasks - ML model training, evaluation, and deployment.

Integrates with the Training Plane (TrainerEngine), Deployment Plane
(DeploymentManager), and Evaluation Plane (ModelEvaluator).

Flow:
  API → Celery → Trainer → Evaluator → Deployment Manager

Design:
- NO business logic in tasks - all logic lives in service/ML layer
- Tasks are thin wrappers that:
  1. Instantiate the appropriate engine/manager
  2. Call its public API
  3. Return the result
- Structured JSON logging for traceability
- Async-safe DB sessions via sessionmaker
"""

from __future__ import annotations

import json
from typing import Any, Optional
from uuid import UUID

from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.workers.celery_app import celery_app

from ml.deployment.deployment_manager import DeploymentManager
from ml.evaluation.evaluator import ModelEvaluator
from ml.training.trainer import TrainerEngine, TrainingConfig

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Session factory - shared across all model tasks
# ---------------------------------------------------------------------------

def _get_session_factory() -> sessionmaker:
    """
    Create a SQLAlchemy session factory from the application settings.

    Uses the synchronous database URL since Celery tasks run synchronously.
    Each task gets its own session to ensure transaction isolation.
    """
    engine = create_engine(
        settings.database_sync_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    return sessionmaker(bind=engine)


def _create_trainer() -> TrainerEngine:
    """Create a TrainerEngine instance with a fresh session factory."""
    session_factory = _get_session_factory()
    return TrainerEngine(session_factory=session_factory)


def _create_evaluator() -> ModelEvaluator:
    """Create a ModelEvaluator instance."""
    return ModelEvaluator(random_seed=42)


def _create_deployment_manager() -> DeploymentManager:
    """Create a DeploymentManager instance with a fresh session factory."""
    session_factory = _get_session_factory()
    return DeploymentManager(session_factory=session_factory)


# ---------------------------------------------------------------------------
# Base Task
# ---------------------------------------------------------------------------


class ModelTask(Task):
    """Base model task with common functionality."""

    auto_retry_for = (Exception,)
    max_retries = 2
    default_retry_delay = 120

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


# ---------------------------------------------------------------------------
# Training Task
# ---------------------------------------------------------------------------


@celery_app.task(
    base=ModelTask,
    bind=True,
    name="train_model_task",
    queue="model_training_queue",
    priority=3,
    max_retries=2,
    default_retry_delay=120,
    retry_backoff=True,
    retry_backoff_max=1800,
    retry_jitter=True,
    acks_late=True,
    reject_on_worker_lose=True,
)
def train_model_task(
    self: Task,
    model_name: str,
    model_type: str,
    version: int = 1,
    hyperparameters: Optional[dict[str, Any]] = None,
    dataset_config: Optional[dict[str, Any]] = None,
    training_config: Optional[dict[str, Any]] = None,
    experiment_name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Train an ML model using the TrainerEngine.

    Delegates all training logic to the TrainerEngine.
    The task is a thin wrapper that:
    1. Builds the TrainingConfig from task parameters
    2. Calls TrainerEngine.train_model()
    3. Returns the serialized result

    Args:
        model_name: Name of the model to train.
        model_type: Type of model (random_forest, xgboost, etc.).
        version: Model version number.
        hyperparameters: Model hyperparameters.
        dataset_config: Dataset configuration.
        training_config: Training configuration.
        experiment_name: Optional experiment name for tracking.
        description: Model description.
        tags: Model tags.

    Returns:
        Training result dict with model_version_id, metrics, artifact path, etc.
    """
    logger.info(
        "model.training.started",
        task_id=self.request.id,
        model_name=model_name,
        model_type=model_type,
        version=version,
    )

    try:
        # Build training config
        config = TrainingConfig(
            model_name=model_name,
            model_type=model_type,
            version=version,
            hyperparameters=hyperparameters or {},
            dataset_config=dataset_config or {},
            training_config=training_config or {},
            random_seed=42,
            experiment_name=experiment_name,
            description=description,
            tags=tags or [],
        )

        # Execute training via TrainerEngine
        trainer = _create_trainer()
        result = trainer.train_model(config)

        # Return serializable result
        serialized_result = {
            "training_run_id": result.training_run_id,
            "model_version_id": result.model_version_id,
            "model_name": result.model_name,
            "model_type": result.model_type,
            "version": result.version,
            "artifact_path": result.artifact_path,
            "checksum": result.checksum,
            "duration_seconds": result.duration_seconds,
            "metrics": {
                "accuracy": result.evaluation_result.accuracy,
                "precision": result.evaluation_result.precision,
                "recall": result.evaluation_result.recall,
                "f1_score": result.evaluation_result.f1_score,
                "roc_auc": result.evaluation_result.roc_auc,
                "pr_auc": result.evaluation_result.pr_auc,
                "false_positive_rate": result.evaluation_result.false_positive_rate,
                "false_negative_rate": result.evaluation_result.false_negative_rate,
                "latency_mean_ms": result.evaluation_result.latency_mean_ms,
            },
            "hyperparameters": result.hyperparameters,
            "environment_hash": result.environment_hash,
            "status": result.status,
            "experiment_id": result.experiment_id,
        }

        logger.info(
            "model.training.completed",
            task_id=self.request.id,
            model_name=model_name,
            f1_score=result.evaluation_result.f1_score,
            duration_s=result.duration_seconds,
        )

        return serialized_result

    except Exception as exc:
        logger.error(
            "model.training.error",
            task_id=self.request.id,
            model_name=model_name,
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=min(120 * (2 ** self.request.retries), 1800))


# ---------------------------------------------------------------------------
# Evaluation Task
# ---------------------------------------------------------------------------


@celery_app.task(
    base=ModelTask,
    bind=True,
    name="evaluate_model_task",
    queue="model_training_queue",
    priority=3,
    max_retries=2,
    default_retry_delay=120,
    retry_backoff=True,
    retry_backoff_max=1800,
    retry_jitter=True,
    acks_late=True,
    reject_on_worker_lose=True,
)
def evaluate_model_task(self: Task, model_version_id: str) -> dict[str, Any]:
    """
    Evaluate an existing model version.

    Loads the model from its artifact and runs comprehensive evaluation
    using the ModelEvaluator.

    Args:
        model_version_id: UUID of the ModelVersion to evaluate.

    Returns:
        Evaluation metrics dict.
    """
    logger.info(
        "model.evaluation.started",
        task_id=self.request.id,
        model_version_id=model_version_id,
    )

    try:
        # Load model version from DB to get artifact path and model type
        session_factory = _get_session_factory()
        with session_factory() as session:
            from app.models.ml.model_version import ModelVersion
            from app.models.ml.enums import ModelStatus

            model_version = (
                session.query(ModelVersion)
                .filter(ModelVersion.id == model_version_id)
                .first()
            )

            if model_version is None:
                raise ValueError(f"ModelVersion not found: {model_version_id}")

            artifact_path = model_version.artifact_path
            algorithm = model_version.algorithm.value
            model_name = model_version.model_name
            version = model_version.version

        # Map algorithm to model type
        model_type_map = {
            "random_forest": "random_forest",
            "xgboost": "xgboost",
            "logistic_regression": "logistic_regression",
            "isolation_forest": "isolation_forest",
        }
        model_type = model_type_map.get(algorithm, "random_forest")

        # Load model from artifact
        from ml.training.trainer import ModelFactory
        model = ModelFactory.load_model_from_artifact(artifact_path, model_type)

        # Build a small test dataset from the training data
        # In production, the test set would be persisted alongside the model
        from ml.training.dataset_builder import DatasetBuilder
        dataset_builder = DatasetBuilder(session_factory=session_factory)
        dataset_version = dataset_builder.build_dataset(
            end_date=None,
            balance_classes=False,
        )
        df = dataset_builder.load_dataset(dataset_version.storage_path)
        split = dataset_builder.split_dataset(df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)

        # Evaluate
        evaluator = _create_evaluator()
        evaluation_result = evaluator.evaluate_model(
            model=model,
            X_test=split.X_test,
            y_test=split.y_test,
            model_name=model_name,
            model_version=version,
            X_train=split.X_train,
            y_train=split.y_train,
            perform_cross_validation=True,
            compute_feature_importance=True,
        )

        # Return serializable result
        result = {
            "model_version_id": model_version_id,
            "model_name": model_name,
            "version": version,
            "status": "evaluated",
            "metrics": {
                "accuracy": evaluation_result.accuracy,
                "precision": evaluation_result.precision,
                "recall": evaluation_result.recall,
                "f1_score": evaluation_result.f1_score,
                "roc_auc": evaluation_result.roc_auc,
                "pr_auc": evaluation_result.pr_auc,
                "false_positive_rate": evaluation_result.false_positive_rate,
                "false_negative_rate": evaluation_result.false_negative_rate,
                "latency_mean_ms": evaluation_result.latency_mean_ms,
                "latency_p95_ms": evaluation_result.latency_p95_ms,
                "latency_p99_ms": evaluation_result.latency_p99_ms,
            },
            "feature_importance": evaluation_result.feature_importance,
        }

        logger.info(
            "model.evaluation.completed",
            task_id=self.request.id,
            model_version_id=model_version_id,
            f1_score=evaluation_result.f1_score,
        )

        return result

    except Exception as exc:
        logger.error(
            "model.evaluation.error",
            task_id=self.request.id,
            model_version_id=model_version_id,
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=min(120 * (2 ** self.request.retries), 1800))


# ---------------------------------------------------------------------------
# Deployment Task
# ---------------------------------------------------------------------------


@celery_app.task(
    base=ModelTask,
    bind=True,
    name="deploy_model_task",
    queue="model_training_queue",
    priority=3,
    max_retries=2,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    acks_late=True,
    reject_on_worker_lose=True,
)
def deploy_model_task(
    self: Task,
    model_version_id: str,
    target_environment: str = "production",
    skip_staging: bool = False,
) -> dict[str, Any]:
    """
    Deploy a model version to a target environment.

    Delegates to DeploymentManager which handles atomic deployment,
    production model demotion, and environment tracking.

    Args:
        model_version_id: UUID of the ModelVersion to deploy.
        target_environment: Target environment (staging, canary, production).
        skip_staging: If True, deploy directly to production.

    Returns:
        Deployment result dict.
    """
    logger.info(
        "model.deployment.started",
        task_id=self.request.id,
        model_version_id=model_version_id,
        target_environment=target_environment,
        skip_staging=skip_staging,
    )

    try:
        deployment_manager = _create_deployment_manager()

        result = deployment_manager.deploy_model(
            model_version_id=model_version_id,
            target_environment=target_environment,
            skip_staging=skip_staging,
        )

        serialized_result = {
            "model_version_id": result.model_version_id,
            "model_name": result.model_name,
            "version": result.version,
            "previous_version_id": result.previous_version_id,
            "previous_version": result.previous_version,
            "target_environment": result.target_environment,
            "status": result.status,
            "timestamp": result.timestamp,
            "metadata": result.metadata,
        }

        logger.info(
            "model.deployment.completed",
            task_id=self.request.id,
            model_version_id=model_version_id,
            status=result.status,
            environment=target_environment,
        )

        return serialized_result

    except Exception as exc:
        logger.error(
            "model.deployment.error",
            task_id=self.request.id,
            model_version_id=model_version_id,
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=min(60 * (2 ** self.request.retries), 600))


# ---------------------------------------------------------------------------
# Rollback Task
# ---------------------------------------------------------------------------


@celery_app.task(
    base=ModelTask,
    bind=True,
    name="rollback_model_task",
    queue="model_training_queue",
    priority=3,
    max_retries=2,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    acks_late=True,
    reject_on_worker_lose=True,
)
def rollback_model_task(
    self: Task,
    model_name: str,
    target_version: Optional[int] = None,
) -> dict[str, Any]:
    """
    Rollback a model to a previous version.

    Delegates to DeploymentManager which handles atomic rollback:
    - Demotes current production model
    - Promotes target (or previous) version to production
    - All within a single DB transaction

    Args:
        model_name: Name of the model to rollback.
        target_version: Optional specific version to rollback to.

    Returns:
        Rollback result dict.
    """
    logger.info(
        "model.rollback.started",
        task_id=self.request.id,
        model_name=model_name,
        target_version=target_version,
    )

    try:
        deployment_manager = _create_deployment_manager()

        result = deployment_manager.rollback_model(
            model_name=model_name,
            target_version=target_version,
        )

        serialized_result = {
            "model_version_id": result.model_version_id,
            "model_name": result.model_name,
            "version": result.version,
            "previous_version_id": result.previous_version_id,
            "previous_version": result.previous_version,
            "target_environment": result.target_environment,
            "status": result.status,
            "timestamp": result.timestamp,
            "metadata": result.metadata,
        }

        logger.info(
            "model.rollback.completed",
            task_id=self.request.id,
            model_name=model_name,
            rolled_back_to_version=result.version,
        )

        return serialized_result

    except Exception as exc:
        logger.error(
            "model.rollback.error",
            task_id=self.request.id,
            model_name=model_name,
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=min(60 * (2 ** self.request.retries), 600))


# ---------------------------------------------------------------------------
# Promote to Staging Task
# ---------------------------------------------------------------------------


@celery_app.task(
    base=ModelTask,
    bind=True,
    name="promote_model_to_staging_task",
    queue="model_training_queue",
    priority=3,
    max_retries=2,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    acks_late=True,
    reject_on_worker_lose=True,
)
def promote_model_to_staging_task(self: Task, model_version_id: str) -> dict[str, Any]:
    """
    Promote a model version to staging environment.

    Args:
        model_version_id: UUID of the ModelVersion to stage.

    Returns:
        Deployment result dict.
    """
    logger.info(
        "model.promote.staging.started",
        task_id=self.request.id,
        model_version_id=model_version_id,
    )

    try:
        deployment_manager = _create_deployment_manager()
        result = deployment_manager.promote_model_to_staging(model_version_id)

        serialized_result = {
            "model_version_id": result.model_version_id,
            "model_name": result.model_name,
            "version": result.version,
            "target_environment": "staging",
            "status": result.status,
            "timestamp": result.timestamp,
        }

        logger.info(
            "model.promote.staging.completed",
            task_id=self.request.id,
            model_version_id=model_version_id,
        )

        return serialized_result

    except Exception as exc:
        logger.error(
            "model.promote.staging.error",
            task_id=self.request.id,
            model_version_id=model_version_id,
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=min(60 * (2 ** self.request.retries), 600))


# ---------------------------------------------------------------------------
# Promote to Production Task
# ---------------------------------------------------------------------------


@celery_app.task(
    base=ModelTask,
    bind=True,
    name="promote_model_to_production_task",
    queue="model_training_queue",
    priority=3,
    max_retries=2,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    acks_late=True,
    reject_on_worker_lose=True,
)
def promote_model_to_production_task(self: Task, model_version_id: str) -> dict[str, Any]:
    """
    Promote a staged model version to production.

    The model must be in STAGED status to be promoted.

    Args:
        model_version_id: UUID of the ModelVersion to promote.

    Returns:
        Deployment result dict.
    """
    logger.info(
        "model.promote.production.started",
        task_id=self.request.id,
        model_version_id=model_version_id,
    )

    try:
        deployment_manager = _create_deployment_manager()
        result = deployment_manager.promote_model_to_production(model_version_id)

        serialized_result = {
            "model_version_id": result.model_version_id,
            "model_name": result.model_name,
            "version": result.version,
            "previous_version_id": result.previous_version_id,
            "previous_version": result.previous_version,
            "target_environment": "production",
            "status": result.status,
            "timestamp": result.timestamp,
        }

        logger.info(
            "model.promote.production.completed",
            task_id=self.request.id,
            model_version_id=model_version_id,
        )

        return serialized_result

    except Exception as exc:
        logger.error(
            "model.promote.production.error",
            task_id=self.request.id,
            model_version_id=model_version_id,
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=min(60 * (2 ** self.request.retries), 600))
