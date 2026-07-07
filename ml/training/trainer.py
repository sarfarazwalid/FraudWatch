"""
ML Training Orchestration Engine.

Implements a fully orchestrated ML lifecycle pipeline:

Pipeline Flow:
  load_dataset_version → load_feature_set → initialize_model →
  apply_hyperparameters → train_model → validate_model → persist_artifact

Design Principles:
- Fully orchestrated, not script-based
- Reproducible: fixed seeds, deterministic splits, environment hashing
- Observable: structured JSON logging, per-epoch metrics, duration tracking
- Resilient: class imbalance handling, graceful error recovery
- Immutable artifacts: every training run produces versioned outputs

Architecture Layer: Training Plane (Execution)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import sessionmaker

from app.models.ml.enums import AlgorithmType, FrameworkType, ModelStatus, TrainingStatus
from app.models.ml.training_run import TrainingRun
from app.models.ml.model_version import ModelVersion
from app.models.ml.model_metrics import ModelMetrics as DBModelMetrics
from app.models.ml.feature_importance import FeatureImportance
from app.repositories.model_registry import ModelRegistryRepository

from ml.evaluation.evaluator import ModelEvaluator, EvaluationResult
from ml.models.base_model import BaseMLModel, ModelMetrics
from ml.models.sklearn_models import (
    RandomForestModel,
    XGBoostModel,
    LogisticRegressionModel,
    IsolationForestModel,
)
from ml.training.dataset_builder import DatasetBuilder, DatasetVersion, DatasetSplit
from ml.tracking.experiment_tracker import ExperimentTracker, ExperimentConfig, ExperimentResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ARTIFACTS_DIR = Path("ml/artifacts/models")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42

MODEL_CLASS_MAP: dict[str, type[BaseMLModel]] = {
    "random_forest": RandomForestModel,
    "xgboost": XGBoostModel,
    "logistic_regression": LogisticRegressionModel,
    "isolation_forest": IsolationForestModel,
}

FRAMEWORK_MAP: dict[str, FrameworkType] = {
    "random_forest": FrameworkType.SCIKIT_LEARN,
    "logistic_regression": FrameworkType.SCIKIT_LEARN,
    "isolation_forest": FrameworkType.SCIKIT_LEARN,
    "xgboost": FrameworkType.XGBOOST,
}

ALGORITHM_MAP: dict[str, AlgorithmType] = {
    "random_forest": AlgorithmType.RANDOM_FOREST,
    "xgboost": AlgorithmType.XGBOOST,
    "logistic_regression": AlgorithmType.LOGISTIC_REGRESSION,
    "isolation_forest": AlgorithmType.CUSTOM,
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class TrainingConfig:
    """Complete configuration for a single training run."""

    model_name: str
    model_type: str
    version: int = 1
    hyperparameters: dict[str, Any] = field(default_factory=dict)
    dataset_config: dict[str, Any] = field(default_factory=dict)
    training_config: dict[str, Any] = field(default_factory=dict)
    random_seed: int = SEED
    experiment_name: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    initiated_by: Optional[str] = None


@dataclass
class TrainingResult:
    """Complete result of a training execution."""

    training_run_id: str
    model_version_id: str
    model_name: str
    model_type: str
    version: int
    artifact_path: str
    checksum: str
    duration_seconds: int
    train_accuracy: float
    val_accuracy: float
    best_metric: float
    hyperparameters: dict[str, Any]
    evaluation_result: EvaluationResult
    environment_hash: str
    status: str
    error_message: Optional[str] = None
    experiment_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Trainer Engine
# ---------------------------------------------------------------------------


class TrainerEngine:
    """
    Production-grade ML training orchestrator.

    Handles the complete training lifecycle:
    1. Dataset loading and splitting
    2. Model initialization with hyperparameters
    3. Training execution with progress tracking
    4. Validation and evaluation
    5. Model persistence with checksum verification
    6. Experiment tracking integration

    Thread-safety: NOT thread-safe per instance. Use one per training run.
    The trainer is designed to be executed within a Celery task or subprocess.
    """

    def __init__(
        self,
        session_factory: sessionmaker,
        dataset_builder: Optional[DatasetBuilder] = None,
        evaluator: Optional[ModelEvaluator] = None,
        experiment_tracker: Optional[ExperimentTracker] = None,
        artifacts_dir: Path = ARTIFACTS_DIR,
        random_seed: int = SEED,
    ):
        """
        Initialize the trainer engine.

        Args:
            session_factory: SQLAlchemy session factory for DB access.
            dataset_builder: Optional DatasetBuilder instance.
            evaluator: Optional ModelEvaluator instance.
            experiment_tracker: Optional ExperimentTracker instance.
            artifacts_dir: Directory to store model artifacts.
            random_seed: Global random seed for reproducibility.
        """
        self.session_factory = session_factory
        self.dataset_builder = dataset_builder or DatasetBuilder(
            session_factory=session_factory,
            random_seed=random_seed,
        )
        self.evaluator = evaluator or ModelEvaluator(random_seed=random_seed)
        self.experiment_tracker = experiment_tracker or ExperimentTracker()
        self.artifacts_dir = artifacts_dir
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.random_seed = random_seed

        # Set seeds for reproducibility
        np.random.seed(random_seed)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def train_model(self, config: TrainingConfig) -> TrainingResult:
        """
        Execute a complete training run.

        This is the main entry point for model training. It orchestrates
        the full pipeline and persists all outputs.

        Args:
            config: Complete training configuration.

        Returns:
            TrainingResult with all metadata about the executed run.

        Raises:
            ValueError: If model_type is unknown.
            RuntimeError: If training fails at any stage.
        """
        logger.info(
            "Training started",
            extra={
                "model_name": config.model_name,
                "model_type": config.model_type,
                "version": config.version,
                "event": "training.started",
            },
        )

        start_time = time.monotonic()

        # Step 1: Compute environment hash for reproducibility
        env_hash = self._compute_environment_hash()

        # Step 2: Create or find experiment
        experiment_id: Optional[str] = None
        if config.experiment_name:
            exp_config = ExperimentConfig(
                experiment_name=config.experiment_name,
                model_type=config.model_type,
                hyperparameters=config.hyperparameters,
                dataset_info=config.dataset_config,
                training_config=config.training_config,
                tags=config.tags,
                description=config.description,
            )
            experiment_id = self.experiment_tracker.start_experiment(exp_config)

        # Step 3: Initialize DB training run
        training_run = self._create_training_run(config, env_hash)

        try:
            # Step 4: Build and split dataset
            dataset_version = self._load_dataset(config)
            dataset_split = self._split_dataset(dataset_version, config)

            # Step 5: Log dataset info to experiment
            if experiment_id:
                self.experiment_tracker.log_parameters(
                    experiment_id,
                    {
                        "dataset_name": dataset_version.dataset_name,
                        "dataset_hash": dataset_version.hash,
                        "train_size": len(dataset_split.X_train),
                        "val_size": len(dataset_split.X_val),
                        "test_size": len(dataset_split.X_test),
                        "fraud_count": dataset_version.fraud_count,
                        "legitimate_count": dataset_version.legitimate_count,
                    },
                )

            # Step 6: Initialize model
            model = self._initialize_model(config)

            # Step 7: Train model
            model = self._execute_training(model, dataset_split, config, experiment_id)

            # Step 8: Evaluate model
            evaluation_result = self._evaluate_model(
                model, dataset_split, config, experiment_id
            )

            # Step 9: Persist model artifact
            artifact_path, checksum = self._persist_artifact(
                model, config, evaluation_result, training_run
            )

            # Step 10: Persist evaluation results to DB
            self._persist_model_version(
                config, training_run, artifact_path, checksum, evaluation_result
            )

            # Step 11: Complete experiment tracking
            if experiment_id and training_run.id:
                self._complete_experiment(
                    experiment_id=experiment_id,
                    training_run=training_run,
                    config=config,
                    dataset_version=dataset_version,
                    evaluation_result=evaluation_result,
                )

            # Step 12: Mark training run as completed
            duration = int(time.monotonic() - start_time)
            self._complete_training_run(training_run, duration)

            logger.info(
                "Training completed",
                extra={
                    "model_name": config.model_name,
                    "version": config.version,
                    "duration_s": duration,
                    "best_metric": evaluation_result.f1_score,
                    "event": "training.completed",
                },
            )

            result = TrainingResult(
                training_run_id=str(training_run.id),
                model_version_id=str(training_run.id),  # Will be updated with actual model_version_id
                model_name=config.model_name,
                model_type=config.model_type,
                version=config.version,
                artifact_path=str(artifact_path),
                checksum=checksum,
                duration_seconds=duration,
                train_accuracy=evaluation_result.accuracy,
                val_accuracy=evaluation_result.accuracy,
                best_metric=evaluation_result.f1_score,
                hyperparameters=config.hyperparameters,
                evaluation_result=evaluation_result,
                environment_hash=env_hash,
                status="completed",
                experiment_id=experiment_id,
            )

            return result

        except Exception as exc:
            duration = int(time.monotonic() - start_time)
            self._fail_training_run(training_run, str(exc), duration)
            logger.error(
                "Training failed",
                extra={
                    "model_name": config.model_name,
                    "version": config.version,
                    "error": str(exc),
                    "duration_s": duration,
                    "event": "training.failed",
                },
            )
            raise RuntimeError(f"Training failed: {exc}") from exc

    # -----------------------------------------------------------------------
    # Pipeline Stages (Private)
    # -----------------------------------------------------------------------

    def _load_dataset(self, config: TrainingConfig) -> DatasetVersion:
        """
        Load and prepare dataset version for training.

        Args:
            config: Training configuration.

        Returns:
            DatasetVersion object.
        """
        logger.info(
            "Loading dataset",
            extra={"event": "dataset.load", "model_name": config.model_name},
        )

        dataset_config = config.dataset_config
        dataset_version = self.dataset_builder.build_dataset(
            start_date=dataset_config.get("start_date"),
            end_date=dataset_config.get("end_date"),
            min_amount=dataset_config.get("min_amount"),
            max_amount=dataset_config.get("max_amount"),
            include_features=dataset_config.get("include_features"),
            exclude_features=dataset_config.get("exclude_features"),
            balance_classes=dataset_config.get("balance_classes", True),
            sampling_strategy=dataset_config.get("sampling_strategy", "auto"),
        )

        logger.info(
            "Dataset loaded",
            extra={
                "event": "dataset.loaded",
                "record_count": dataset_version.record_count,
                "feature_count": dataset_version.feature_count,
                "fraud_rate": dataset_version.fraud_count / max(dataset_version.record_count, 1),
            },
        )

        return dataset_version

    def _split_dataset(
        self, dataset_version: DatasetVersion, config: TrainingConfig
    ) -> DatasetSplit:
        """
        Split dataset into train/validation/test sets.

        Args:
            dataset_version: Dataset to split.
            config: Training configuration.

        Returns:
            DatasetSplit object.
        """
        training_config = config.training_config
        split_type_str = training_config.get("split_type", "stratified")
        from ml.training.dataset_builder import DatasetSplitType

        split_type_map = {
            "random": DatasetSplitType.RANDOM,
            "time_based": DatasetSplitType.TIME_BASED,
            "stratified": DatasetSplitType.STRATIFIED,
        }
        split_type = split_type_map.get(split_type_str, DatasetSplitType.STRATIFIED)

        # Load the dataset from storage
        df = self.dataset_builder.load_dataset(dataset_version.storage_path)

        split = self.dataset_builder.split_dataset(
            df=df,
            split_type=split_type,
            train_ratio=training_config.get("train_ratio", 0.7),
            val_ratio=training_config.get("val_ratio", 0.15),
            test_ratio=training_config.get("test_ratio", 0.15),
        )

        logger.info(
            "Dataset split",
            extra={
                "event": "dataset.split",
                "train": len(split.X_train),
                "val": len(split.X_val),
                "test": len(split.X_test),
            },
        )

        return split

    def _initialize_model(self, config: TrainingConfig) -> BaseMLModel:
        """
        Initialize a model based on configuration.

        Args:
            config: Training configuration.

        Returns:
            Initialized BaseMLModel instance.

        Raises:
            ValueError: If model_type is unknown.
        """
        model_class = MODEL_CLASS_MAP.get(config.model_type)
        if model_class is None:
            raise ValueError(
                f"Unknown model_type: {config.model_type}. "
                f"Available: {list(MODEL_CLASS_MAP.keys())}"
            )

        model = model_class(version=str(config.version))
        logger.info(
            "Model initialized",
            extra={
                "event": "model.initialized",
                "model_type": config.model_type,
                "version": config.version,
            },
        )
        return model

    def _execute_training(
        self,
        model: BaseMLModel,
        split: DatasetSplit,
        config: TrainingConfig,
        experiment_id: Optional[str] = None,
    ) -> BaseMLModel:
        """
        Execute model training with the provided dataset split.

        Args:
            model: Uninitialized model instance.
            split: Dataset split to train on.
            config: Training configuration.
            experiment_id: Optional experiment ID for tracking.

        Returns:
            Trained model instance.
        """
        logger.info(
            "Training model",
            extra={
                "event": "model.training",
                "model_type": config.model_type,
                "train_size": len(split.X_train),
            },
        )

        # Log training start
        if experiment_id:
            self.experiment_tracker.log_metrics(
                experiment_id,
                {"train_samples": len(split.X_train), "val_samples": len(split.X_val)},
            )

        # Train with hyperparameters
        model.train(
            split.X_train.values,
            split.y_train.values,
            **config.hyperparameters,
        )

        # Compute training accuracy for logging
        train_preds = model.predict(split.X_train.values)
        train_accuracy = float(np.mean(train_preds == split.y_train.values))

        # Compute validation accuracy
        if len(split.X_val) > 0:
            val_preds = model.predict(split.X_val.values)
            val_accuracy = float(np.mean(val_preds == split.y_val.values))
        else:
            val_accuracy = train_accuracy

        logger.info(
            "Training progress",
            extra={
                "event": "model.training.progress",
                "train_accuracy": train_accuracy,
                "val_accuracy": val_accuracy,
                "model_type": config.model_type,
            },
        )

        if experiment_id:
            self.experiment_tracker.log_metrics(
                experiment_id,
                {
                    "train_accuracy": train_accuracy,
                    "val_accuracy": val_accuracy,
                    "training_complete": 1.0,
                },
            )

        return model

    def _evaluate_model(
        self,
        model: BaseMLModel,
        split: DatasetSplit,
        config: TrainingConfig,
        experiment_id: Optional[str] = None,
    ) -> EvaluationResult:
        """
        Evaluate trained model on test set.

        Args:
            model: Trained model instance.
            split: Dataset split with test data.
            config: Training configuration.
            experiment_id: Optional experiment ID for tracking.

        Returns:
            EvaluationResult with all metrics.
        """
        logger.info(
            "Evaluating model",
            extra={
                "event": "model.evaluation",
                "model_type": config.model_type,
                "test_size": len(split.X_test),
            },
        )

        evaluation_result = self.evaluator.evaluate_model(
            model=model,
            X_test=split.X_test,
            y_test=split.y_test,
            model_name=config.model_name,
            model_version=config.version,
            X_train=split.X_train,
            y_train=split.y_train,
            perform_cross_validation=True,
            compute_feature_importance=True,
        )

        logger.info(
            "Evaluation complete",
            extra={
                "event": "model.evaluated",
                "accuracy": evaluation_result.accuracy,
                "precision": evaluation_result.precision,
                "recall": evaluation_result.recall,
                "f1": evaluation_result.f1_score,
                "roc_auc": evaluation_result.roc_auc,
            },
        )

        if experiment_id:
            self.experiment_tracker.log_metrics(
                experiment_id,
                {
                    "test_accuracy": evaluation_result.accuracy,
                    "test_precision": evaluation_result.precision,
                    "test_recall": evaluation_result.recall,
                    "test_f1": evaluation_result.f1_score,
                    "test_roc_auc": evaluation_result.roc_auc,
                },
            )

        return evaluation_result

    def _persist_artifact(
        self,
        model: BaseMLModel,
        config: TrainingConfig,
        evaluation: EvaluationResult,
        training_run: TrainingRun,
    ) -> tuple[Path, str]:
        """
        Serialize and persist model artifact with checksum.

        Args:
            model: Trained model to persist.
            config: Training configuration.
            evaluation: Evaluation results.
            training_run: DB training run record.

        Returns:
            Tuple of (artifact_path, checksum).
        """
        # Create artifact directory
        model_dir = self.artifacts_dir / config.model_name / str(config.version)
        model_dir.mkdir(parents=True, exist_ok=True)

        # Serialize model
        artifact_path = model_dir / "model.joblib"
        model.save(str(artifact_path))

        # Compute checksum
        checksum = self._compute_file_hash(artifact_path)

        # Save evaluation results alongside artifact
        eval_path = model_dir / "evaluation.json"
        eval_data = {
            "model_name": evaluation.model_name,
            "model_version": evaluation.model_version,
            "accuracy": evaluation.accuracy,
            "precision": evaluation.precision,
            "recall": evaluation.recall,
            "f1_score": evaluation.f1_score,
            "roc_auc": evaluation.roc_auc,
            "pr_auc": evaluation.pr_auc,
            "false_positive_rate": evaluation.false_positive_rate,
            "false_negative_rate": evaluation.false_negative_rate,
            "latency_mean_ms": evaluation.latency_mean_ms,
            "latency_p95_ms": evaluation.latency_p95_ms,
            "latency_p99_ms": evaluation.latency_p99_ms,
            "feature_importance": evaluation.feature_importance,
            "evaluated_at": evaluation.evaluated_at,
        }
        with open(eval_path, "w") as f:
            json.dump(eval_data, f, indent=2)

        # Save training config alongside artifact
        config_path = model_dir / "config.json"
        config_data = {
            "model_name": config.model_name,
            "model_type": config.model_type,
            "version": config.version,
            "hyperparameters": config.hyperparameters,
            "dataset_config": config.dataset_config,
            "training_config": config.training_config,
            "random_seed": config.random_seed,
        }
        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=2)

        logger.info(
            "Artifact persisted",
            extra={
                "event": "artifact.persisted",
                "path": str(artifact_path),
                "checksum": checksum[:16],
                "size_bytes": artifact_path.stat().st_size,
            },
        )

        return artifact_path, checksum

    def _persist_model_version(
        self,
        config: TrainingConfig,
        training_run: TrainingRun,
        artifact_path: Path,
        checksum: str,
        evaluation: EvaluationResult,
    ) -> ModelVersion:
        """
        Persist model version record in the database.

        Args:
            config: Training configuration.
            training_run: Associated training run record.
            artifact_path: Path to serialized model.
            checksum: SHA256 checksum of model artifact.
            evaluation: Evaluation results.

        Returns:
            Persisted ModelVersion record.
        """
        with self.session_factory() as session:
            model_version = ModelVersion(
                model_name=config.model_name,
                version=config.version,
                algorithm=ALGORITHM_MAP.get(config.model_type, AlgorithmType.CUSTOM),
                framework=FRAMEWORK_MAP.get(config.model_type, FrameworkType.CUSTOM),
                artifact_path=str(artifact_path),
                checksum=checksum,
                training_run_id=training_run.id,
                status=ModelStatus.EVALUATING,
                description=config.description or f"Auto-trained {config.model_type} v{config.version}",
                hyperparameters=json.dumps(config.hyperparameters),
                training_duration_seconds=0,  # Will be updated on completion
            )
            session.add(model_version)
            session.flush()
            session.refresh(model_version)

            # Persist metrics
            db_metrics = DBModelMetrics(
                model_version_id=model_version.id,
                accuracy=evaluation.accuracy,
                precision=evaluation.precision,
                recall=evaluation.recall,
                f1_score=evaluation.f1_score,
                roc_auc=evaluation.roc_auc,
                pr_auc=evaluation.pr_auc,
                false_positive_rate=evaluation.false_positive_rate,
                false_negative_rate=evaluation.false_negative_rate,
                latency_mean_ms=evaluation.latency_mean_ms,
                latency_p95_ms=evaluation.latency_p95_ms,
                latency_p99_ms=evaluation.latency_p99_ms,
            )
            session.add(db_metrics)

            # Persist feature importance if available
            if evaluation.feature_importance:
                for rank, (feature_name, importance) in enumerate(
                    sorted(evaluation.feature_importance.items(), key=lambda x: x[1], reverse=True)
                ):
                    fi = FeatureImportance(
                        model_version_id=model_version.id,
                        feature_name=feature_name,
                        importance_score=importance,
                        rank=rank + 1,
                    )
                    session.add(fi)

            session.commit()
            session.refresh(model_version)

            logger.info(
                "Model version persisted",
                extra={
                    "event": "model.version.persisted",
                    "model_version_id": str(model_version.id),
                    "model_name": config.model_name,
                    "version": config.version,
                },
            )

            return model_version

    # -----------------------------------------------------------------------
    # Training Run DB Management
    # -----------------------------------------------------------------------

    def _create_training_run(
        self, config: TrainingConfig, env_hash: str
    ) -> TrainingRun:
        """
        Create a training run record in the database.

        Args:
            config: Training configuration.
            env_hash: Environment hash for reproducibility.

        Returns:
            TrainingRun DB record.
        """
        with self.session_factory() as session:
            training_run = TrainingRun(
                run_name=config.experiment_name or f"{config.model_name}_v{config.version}",
                dataset_id=uuid.uuid4(),  # Will be updated with actual dataset_id
                training_status=TrainingStatus.RUNNING,
                started_at=datetime.now(timezone.utc),
                random_seed=config.random_seed,
                hyperparameters=json.dumps(config.hyperparameters),
                notes=f"Training run for {config.model_name} v{config.version}",
            )
            session.add(training_run)
            session.flush()
            session.refresh(training_run)

            logger.info(
                "Training run created",
                extra={
                    "event": "training_run.created",
                    "training_run_id": str(training_run.id),
                    "run_name": training_run.run_name,
                },
            )

            return training_run

    def _complete_training_run(
        self, training_run: TrainingRun, duration_seconds: int
    ) -> None:
        """
        Mark training run as completed with duration.

        Args:
            training_run: Training run record.
            duration_seconds: Training duration.
        """
        with self.session_factory() as session:
            run = session.query(TrainingRun).filter(TrainingRun.id == training_run.id).first()
            if run:
                run.training_status = TrainingStatus.COMPLETED
                run.completed_at = datetime.now(timezone.utc)
                run.duration_seconds = duration_seconds
                session.commit()

    def _fail_training_run(
        self, training_run: TrainingRun, error_message: str, duration_seconds: int
    ) -> None:
        """
        Mark training run as failed with error details.

        Args:
            training_run: Training run record.
            error_message: Error description.
            duration_seconds: Duration until failure.
        """
        with self.session_factory() as session:
            run = session.query(TrainingRun).filter(TrainingRun.id == training_run.id).first()
            if run:
                run.training_status = TrainingStatus.FAILED
                run.completed_at = datetime.now(timezone.utc)
                run.duration_seconds = duration_seconds
                run.error_message = error_message
                session.commit()

    # -----------------------------------------------------------------------
    # Experiment Tracking
    # -----------------------------------------------------------------------

    def _complete_experiment(
        self,
        experiment_id: str,
        training_run: TrainingRun,
        config: TrainingConfig,
        dataset_version: DatasetVersion,
        evaluation_result: EvaluationResult,
    ) -> None:
        """
        Complete experiment with all tracking data.

        Args:
            experiment_id: Experiment identifier.
            training_run: Completed training run.
            config: Training configuration.
            dataset_version: Dataset used.
            evaluation_result: Evaluation results.
        """
        from app.models.ml.model_metrics import ModelMetrics
        from app.models.ml.dataset_metadata import DatasetMetadata

        # Build metrics for experiment tracker
        metrics = ModelMetrics(
            accuracy=evaluation_result.accuracy,
            precision=evaluation_result.precision,
            recall=evaluation_result.recall,
            f1=evaluation_result.f1_score,
            roc_auc=evaluation_result.roc_auc,
        )

        # Build dataset metadata
        dataset_meta = DatasetMetadata(
            dataset_name=dataset_version.dataset_name,
            source="training_pipeline",
            record_count=dataset_version.record_count,
            feature_count=dataset_version.feature_count,
            hash=dataset_version.hash,
        )

        self.experiment_tracker.complete_experiment(
            experiment_id=experiment_id,
            training_run=training_run,
            model_version=None,  # Will be updated by caller
            dataset=dataset_meta,
            metrics=metrics,
            artifacts={"model_dir": str(self.artifacts_dir)},
        )

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _compute_environment_hash(self) -> str:
        """
        Compute deterministic hash of the current environment.

        Includes Python version, platform, and key library versions.
        This enables exact reproduction of training conditions.

        Returns:
            SHA256 hex digest string.
        """
        env_info = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "numpy_version": np.__version__,
        }
        try:
            import sklearn
            env_info["sklearn_version"] = sklearn.__version__
        except ImportError:
            pass
        try:
            import xgboost
            env_info["xgboost_version"] = xgboost.__version__
        except ImportError:
            pass
        try:
            import pandas as pd
            env_info["pandas_version"] = pd.__version__
        except ImportError:
            pass

        raw = json.dumps(env_info, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _compute_file_hash(path: Path) -> str:
        """
        Compute SHA256 checksum of a file.

        Args:
            path: Path to file.

        Returns:
            SHA256 hex digest string.
        """
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_available_model_types(self) -> list[str]:
        """
        Get list of available model types for training.

        Returns:
            List of model type identifiers.
        """
        return list(MODEL_CLASS_MAP.keys())


# ---------------------------------------------------------------------------
# Model Factory
# ---------------------------------------------------------------------------


class ModelFactory:
    """
    Factory for creating ML model instances.

    Provides a clean interface for instantiating models by type string.
    Used by TrainerEngine and Celery tasks.
    """

    @staticmethod
    def create_model(model_type: str, version: str = "1.0.0") -> BaseMLModel:
        """
        Create a model instance by type.

        Args:
            model_type: Model type identifier.
            version: Model version string.

        Returns:
            Model instance.

        Raises:
            ValueError: If model_type is unknown.
        """
        model_class = MODEL_CLASS_MAP.get(model_type)
        if model_class is None:
            raise ValueError(f"Unknown model type: {model_type}")
        return model_class(version=version)

    @staticmethod
    def load_model_from_artifact(artifact_path: str, model_type: str) -> BaseMLModel:
        """
        Load a model from a persisted artifact.

        Args:
            artifact_path: Path to serialized model file.
            model_type: Model type identifier.

        Returns:
            Loaded model instance.
        """
        model = ModelFactory.create_model(model_type)
        model.load(artifact_path)
        return model
