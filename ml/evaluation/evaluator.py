"""
Model evaluation engine for ML lifecycle management.

Computes comprehensive metrics for trained models and stores results
in the ModelMetrics table for tracking and comparison.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    roc_curve,
    precision_recall_curve,
)
from sklearn.model_selection import cross_val_score, StratifiedKFold

from app.models.ml.model_metrics import ModelMetrics


logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Model evaluation results with comprehensive metrics."""

    model_name: str
    model_version: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    pr_auc: float
    confusion_matrix: np.ndarray
    false_positive_rate: float
    false_negative_rate: float
    latency_mean_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    cross_val_scores: Optional[np.ndarray] = None
    feature_importance: Optional[dict[str, float]] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    evaluated_at: str = field(default_factory=lambda: pd.Timestamp.utcnow().isoformat())


class ModelEvaluator:
    """
    Comprehensive model evaluation engine.

    Computes metrics required for model comparison and deployment decisions.
    Supports cross-validation, latency benchmarking, and feature importance analysis.
    """

    def __init__(
        self,
        threshold: float = 0.5,
        cross_validation_folds: int = 5,
        random_seed: int = 42,
    ):
        """
        Initialize model evaluator.

        Args:
            threshold: Classification threshold for binary predictions
            cross_validation_folds: Number of folds for cross-validation
            random_seed: Random seed for reproducibility
        """
        self.threshold = threshold
        self.cross_validation_folds = cross_validation_folds
        self.random_seed = random_seed

    def evaluate_model(
        self,
        model: Any,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        model_name: str,
        model_version: int,
        X_train: Optional[pd.DataFrame] = None,
        y_train: Optional[pd.Series] = None,
        perform_cross_validation: bool = True,
        compute_feature_importance: bool = True,
    ) -> EvaluationResult:
        """
        Evaluate a trained model on test data.

        Args:
            model: Trained model object
            X_test: Test features
            y_test: Test labels
            model_name: Model identifier
            model_version: Model version number
            X_train: Optional training features for cross-validation
            y_train: Optional training labels for cross-validation
            perform_cross_validation: Whether to run cross-validation
            compute_feature_importance: Whether to compute feature importance

        Returns:
            EvaluationResult with all computed metrics
        """
        logger.info(f"Evaluating model {model_name} v{model_version}")

        # Measure inference latency
        latency_metrics = self._benchmark_latency(model, X_test)

        # Generate predictions
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        y_pred = (y_pred_proba >= self.threshold).astype(int)

        # Compute metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        pr_auc = average_precision_score(y_test, y_pred_proba)

        # Compute confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()

        # Compute rates
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        # Cross-validation
        cv_scores = None
        if perform_cross_validation and X_train is not None and y_train is not None:
            cv_scores = self._cross_validate(model, X_train, y_train)

        # Feature importance
        feature_importance = None
        if compute_feature_importance:
            feature_importance = self._extract_feature_importance(model, X_test.columns)

        result = EvaluationResult(
            model_name=model_name,
            model_version=model_version,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            roc_auc=roc_auc,
            pr_auc=pr_auc,
            confusion_matrix=cm,
            false_positive_rate=fpr,
            false_negative_rate=fnr,
            latency_mean_ms=latency_metrics["mean"],
            latency_p95_ms=latency_metrics["p95"],
            latency_p99_ms=latency_metrics["p99"],
            cross_val_scores=cv_scores,
            feature_importance=feature_importance,
            metadata={
                "threshold": self.threshold,
                "test_size": len(y_test),
                "fraud_rate": float(y_test.mean()),
                "cv_folds": self.cross_validation_folds if perform_cross_validation else None,
            },
        )

        logger.info(
            f"Evaluation complete: accuracy={accuracy:.4f}, precision={precision:.4f}, "
            f"recall={recall:.4f}, f1={f1:.4f}, roc_auc={roc_auc:.4f}"
        )

        return result

    def _benchmark_latency(self, model: Any, X: pd.DataFrame) -> dict[str, float]:
        """
        Benchmark model inference latency.

        Args:
            model: Model to benchmark
            X: Feature matrix for benchmarking

        Returns:
            Dictionary with latency metrics
        """
        # Warmup
        for _ in range(10):
            model.predict_proba(X.iloc[:10])

        # Benchmark
        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            model.predict_proba(X.iloc[:10])
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to milliseconds

        latencies = np.array(latencies)

        return {
            "mean": float(np.mean(latencies)),
            "p95": float(np.percentile(latencies, 95)),
            "p99": float(np.percentile(latencies, 99)),
        }

    def _cross_validate(self, model: Any, X: pd.DataFrame, y: pd.Series) -> np.ndarray:
        """
        Perform stratified k-fold cross-validation.

        Args:
            model: Model to validate
            X: Feature matrix
            y: Labels

        Returns:
            Array of cross-validation scores
        """
        cv = StratifiedKFold(n_splits=self.cross_validation_folds, shuffle=True, random_state=self.random_seed)

        try:
            scores = cross_val_score(model, X, y, cv=cv, scoring="f1", n_jobs=-1)
            logger.info(f"Cross-validation F1 scores: {scores.mean():.4f} (+/- {scores.std():.4f})")
            return scores
        except Exception as e:
            logger.warning(f"Cross-validation failed: {e}")
            return np.array([])

    def _extract_feature_importance(self, model: Any, feature_names: pd.Index) -> dict[str, float]:
        """
        Extract feature importance from model.

        Args:
            model: Trained model
            feature_names: Feature names

        Returns:
            Dictionary mapping feature names to importance scores
        """
        importance_dict = {}

        try:
            # Tree-based models
            if hasattr(model, "feature_importances_"):
                importances = model.feature_importances_
                for name, importance in zip(feature_names, importances):
                    importance_dict[name] = float(importance)

            # Linear models
            elif hasattr(model, "coef_"):
                coef = np.abs(model.coef_[0])
                for name, importance in zip(feature_names, coef):
                    importance_dict[name] = float(importance)

            # Sort by importance
            importance_dict = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))

        except Exception as e:
            logger.warning(f"Could not extract feature importance: {e}")

        return importance_dict

    def compare_models(self, results: list[EvaluationResult]) -> pd.DataFrame:
        """
        Compare multiple model evaluation results.

        Args:
            results: List of EvaluationResult objects

        Returns:
            DataFrame with model comparison
        """
        comparison_data = []

        for result in results:
            comparison_data.append({
                "model_name": result.model_name,
                "model_version": result.model_version,
                "accuracy": result.accuracy,
                "precision": result.precision,
                "recall": result.recall,
                "f1_score": result.f1_score,
                "roc_auc": result.roc_auc,
                "pr_auc": result.pr_auc,
                "false_positive_rate": result.false_positive_rate,
                "false_negative_rate": result.false_negative_rate,
                "latency_mean_ms": result.latency_mean_ms,
                "evaluated_at": result.evaluated_at,
            })

        df = pd.DataFrame(comparison_data)
        return df.sort_values(by="f1_score", ascending=False)

    def generate_classification_report(
        self, result: EvaluationResult, X_test: pd.DataFrame, y_test: pd.Series, model: Any
    ) -> str:
        """
        Generate detailed classification report.

        Args:
            result: EvaluationResult object
            X_test: Test features
            y_test: Test labels
            model: Trained model

        Returns:
            Formatted classification report string
        """
        from sklearn.metrics import classification_report

        y_pred = (model.predict_proba(X_test)[:, 1] >= self.threshold).astype(int)

        report = classification_report(
            y_test,
            y_pred,
            target_names=["Legitimate", "Fraud"],
            digits=4,
        )

        # Add confusion matrix
        report += f"\n\nConfusion Matrix:\n{result.confusion_matrix}\n"
        report += f"\nFalse Positive Rate: {result.false_positive_rate:.4f}"
        report += f"\nFalse Negative Rate: {result.false_negative_rate:.4f}"

        # Add latency metrics
        report += f"\n\nLatency Metrics:"
        report += f"\n  Mean: {result.latency_mean_ms:.2f}ms"
        report += f"\n  P95: {result.latency_p95_ms:.2f}ms"
        report += f"\n  P99: {result.latency_p99_ms:.2f}ms"

        return report
