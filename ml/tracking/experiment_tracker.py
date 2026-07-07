"""
Experiment tracking for ML lifecycle management.

Tracks training experiments with parameters, metrics, and complete lineage
for reproducibility and model comparison.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from app.models.ml.dataset_metadata import DatasetMetadata
from app.models.ml.model_metrics import ModelMetrics
from app.models.ml.model_version import ModelVersion
from app.models.ml.training_run import TrainingRun


logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """Experiment configuration and hyperparameters."""

    experiment_name: str
    model_type: str
    hyperparameters: dict[str, Any]
    dataset_info: dict[str, Any]
    training_config: dict[str, Any]
    tags: list[str] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class ExperimentResult:
    """Complete experiment results with all tracking data."""

    experiment_id: str
    training_run: TrainingRun
    model_version: ModelVersion
    dataset: DatasetMetadata
    metrics: ModelMetrics
    config: ExperimentConfig
    started_at: datetime
    completed_at: datetime
    duration_seconds: int
    status: str
    artifacts: dict[str, str] = field(default_factory=dict)
    notes: Optional[str] = None


class ExperimentTracker:
    """
    Training experiment tracking for ML lifecycle.

    Tracks all aspects of model training experiments:
    - Hyperparameters and configuration
    - Dataset version and lineage
    - Training metrics and evolution
    - Environment and reproducibility info
    - Artifacts and outputs

    Enables full reproducibility and experiment comparison.
    """

    def __init__(self):
        """Initialize experiment tracker."""
        self.experiments: dict[str, ExperimentResult] = {}

    def start_experiment(self, config: ExperimentConfig) -> str:
        """
        Start a new training experiment.

        Args:
            config: Experiment configuration

        Returns:
            Experiment ID
        """
        import uuid

        experiment_id = str(uuid.uuid4())
        logger.info(f"Starting experiment {experiment_id}: {config.experiment_name}")

        # Store experiment metadata
        self.experiments[experiment_id] = {
            "config": config,
            "started_at": datetime.utcnow(),
            "status": "running",
        }

        return experiment_id

    def log_metrics(self, experiment_id: str, metrics: dict[str, float], step: Optional[int] = None) -> None:
        """
        Log training metrics.

        Args:
            experiment_id: Experiment identifier
            metrics: Dictionary of metric names and values
            step: Optional training step/epoch number
        """
        logger.debug(f"Logging metrics for {experiment_id}: {metrics}")

    def log_parameters(self, experiment_id: str, parameters: dict[str, Any]) -> None:
        """
        Log training parameters.

        Args:
            experiment_id: Experiment identifier
            parameters: Dictionary of parameter names and values
        """
        logger.debug(f"Logging parameters for {experiment_id}: {parameters}")

    def log_artifact(self, experiment_id: str, name: str, path: str) -> None:
        """
        Log training artifact path.

        Args:
            experiment_id: Experiment identifier
            name: Artifact name
            path: Path to artifact file
        """
        logger.debug(f"Logging artifact {name} at {path} for {experiment_id}")

    def complete_experiment(
        self,
        experiment_id: str,
        training_run: TrainingRun,
        model_version: ModelVersion,
        dataset: DatasetMetadata,
        metrics: ModelMetrics,
        artifacts: Optional[dict[str, str]] = None,
        notes: Optional[str] = None,
    ) -> ExperimentResult:
        """
        Complete an experiment with final results.

        Args:
            experiment_id: Experiment identifier
            training_run: Completed training run
            model_version: Created model version
            dataset: Dataset used for training
            metrics: Computed model metrics
            artifacts: Dictionary of artifact names and paths
            notes: Additional notes

        Returns:
            ExperimentResult object
        """
        logger.info(f"Completing experiment {experiment_id}")

        result = ExperimentResult(
            experiment_id=experiment_id,
            training_run=training_run,
            model_version=model_version,
            dataset=dataset,
            metrics=metrics,
            config=self.experiments[experiment_id]["config"],
            started_at=self.experiments[experiment_id]["started_at"],
            completed_at=datetime.utcnow(),
            duration_seconds=int((datetime.utcnow() - self.experiments[experiment_id]["started_at"]).total_seconds()),
            status="completed",
            artifacts=artifacts or {},
            notes=notes,
        )

        self.experiments[experiment_id]["result"] = result
        self.experiments[experiment_id]["status"] = "completed"

        return result

    def get_experiment(self, experiment_id: str) -> Optional[ExperimentResult]:
        """
        Get experiment by ID.

        Args:
            experiment_id: Experiment identifier

        Returns:
            ExperimentResult or None
        """
        exp = self.experiments.get(experiment_id)
        return exp.get("result") if exp else None

    def list_experiments(self, model_type: Optional[str] = None) -> list[ExperimentResult]:
        """
        List all experiments, optionally filtered by model type.

        Args:
            model_type: Optional model type filter

        Returns:
            List of ExperimentResult objects
        """
        results = []
        for exp_id, exp_data in self.experiments.items():
            if "result" in exp_data:
                result = exp_data["result"]
                if model_type is None or result.config.model_type == model_type:
                    results.append(result)
        return results

    def compare_experiments(self, experiment_ids: list[str]) -> pd.DataFrame:
        """
        Compare multiple experiments.

        Args:
            experiment_ids: List of experiment IDs to compare

        Returns:
            DataFrame with experiment comparison
        """
        import pandas as pd

        comparison_data = []

        for exp_id in experiment_ids:
            result = self.get_experiment(exp_id)
            if result:
                comparison_data.append({
                    "experiment_id": exp_id,
                    "model_type": result.config.model_type,
                    "accuracy": result.metrics.accuracy,
                    "precision": result.metrics.precision,
                    "recall": result.metrics.recall,
                    "f1_score": result.metrics.f1_score,
                    "roc_auc": result.metrics.roc_auc,
                    "duration_seconds": result.duration_seconds,
                    "completed_at": result.completed_at.isoformat(),
                })

        return pd.DataFrame(comparison_data)

    def get_best_experiment(self, metric: str = "f1_score", model_type: Optional[str] = None) -> Optional[ExperimentResult]:
        """
        Get best experiment by metric.

        Args:
            metric: Metric to optimize
            model_type: Optional model type filter

        Returns:
            Best ExperimentResult or None
        """
        experiments = self.list_experiments(model_type=model_type)

        if not experiments:
            return None

        best = max(
            experiments,
            key=lambda exp: getattr(exp.metrics, metric, float("-inf")),
        )

        return best
