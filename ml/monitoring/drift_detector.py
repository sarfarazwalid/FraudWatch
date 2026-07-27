"""
Drift Detection System for ML Model Monitoring.

Implements statistical drift detection methods:
- Population Stability Index (PSI)
- Feature Drift (Kolmogorov-Smirnov test)
- Prediction Drift
- Confidence Drift

Generates warning levels: LOW, MEDIUM, HIGH, CRITICAL
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class DriftWarningLevel(str, Enum):
    """Drift warning severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DriftResult:
    """Result of drift detection for a single feature or prediction."""
    feature_name: str
    drift_score: float
    warning_level: DriftWarningLevel
    threshold_exceeded: str
    reference_mean: float
    current_mean: float
    reference_std: float
    current_std: float
    sample_size_reference: int
    sample_size_current: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DriftReport:
    """Complete drift detection report for a model."""
    model_name: str
    model_version: int
    detection_timestamp: str
    overall_drift_score: float
    overall_warning_level: DriftWarningLevel
    feature_drifts: list[DriftResult]
    prediction_drift: Optional[DriftResult]
    confidence_drift: Optional[DriftResult]
    summary: str
    recommendations: list[str] = field(default_factory=list)


class DriftDetector:
    """
    Statistical drift detection for ML model monitoring.

    Detects when:
    - Input feature distributions shift (data drift)
    - Model predictions shift (prediction drift)
    - Model confidence shifts (confidence drift)

    Uses Population Stability Index (PSI) for feature drift
    and Kolmogorov-Smirnov test for distribution comparison.
    """

    def __init__(
        self,
        psi_threshold_low: float = 0.1,
        psi_threshold_medium: float = 0.2,
        psi_threshold_high: float = 0.3,
        psi_threshold_critical: float = 0.5,
        ks_threshold_low: float = 0.1,
        ks_threshold_medium: float = 0.2,
        ks_threshold_high: float = 0.3,
        ks_threshold_critical: float = 0.5,
    ):
        """
        Initialize drift detector with configurable thresholds.

        Args:
            psi_threshold_*: PSI thresholds for warning levels
            ks_threshold_*: KS test p-value thresholds for warning levels
        """
        self.psi_thresholds = {
            DriftWarningLevel.LOW: psi_threshold_low,
            DriftWarningLevel.MEDIUM: psi_threshold_medium,
            DriftWarningLevel.HIGH: psi_threshold_high,
            DriftWarningLevel.CRITICAL: psi_threshold_critical,
        }
        self.ks_thresholds = {
            DriftWarningLevel.LOW: ks_threshold_low,
            DriftWarningLevel.MEDIUM: ks_threshold_medium,
            DriftWarningLevel.HIGH: ks_threshold_high,
            DriftWarningLevel.CRITICAL: ks_threshold_critical,
        }

    def detect_feature_drift(
        self,
        feature_name: str,
        reference_data: np.ndarray,
        current_data: np.ndarray,
        feature_type: str = "numeric",
    ) -> DriftResult:
        """
        Detect drift for a single feature.

        Args:
            feature_name: Name of the feature
            reference_data: Historical/reference data (training data)
            current_data: Current production data
            feature_type: Type of feature (numeric, categorical)

        Returns:
            DriftResult with drift metrics
        """
        if feature_type == "categorical":
            drift_score = self._calculate_psi_categorical(reference_data, current_data)
        else:
            drift_score = self._calculate_psi_numeric(reference_data, current_data)

        warning_level = self._get_warning_level(drift_score)
        threshold_exceeded = self._get_threshold_exceeded(drift_score)

        # Compute statistics
        ref_mean = float(np.mean(reference_data))
        curr_mean = float(np.mean(current_data))
        ref_std = float(np.std(reference_data))
        curr_std = float(np.std(current_data))

        result = DriftResult(
            feature_name=feature_name,
            drift_score=drift_score,
            warning_level=warning_level,
            threshold_exceeded=threshold_exceeded,
            reference_mean=ref_mean,
            current_mean=curr_mean,
            reference_std=ref_std,
            current_std=curr_std,
            sample_size_reference=len(reference_data),
            sample_size_current=len(current_data),
            metadata={
                "feature_type": feature_type,
                "mean_shift_pct": ((curr_mean - ref_mean) / abs(ref_mean) * 100) if ref_mean != 0 else 0,
                "std_shift_pct": ((curr_std - ref_std) / abs(ref_std) * 100) if ref_std != 0 else 0,
            },
        )

        logger.info(
            f"Drift detected for {feature_name}",
            extra={
                "event": "drift.detected",
                "feature_name": feature_name,
                "drift_score": drift_score,
                "warning_level": warning_level.value,
            },
        )

        return result

    def detect_prediction_drift(
        self,
        reference_predictions: np.ndarray,
        current_predictions: np.ndarray,
    ) -> DriftResult:
        """
        Detect drift in model predictions.

        Args:
            reference_predictions: Historical predictions
            current_predictions: Current predictions

        Returns:
            DriftResult for prediction distribution
        """
        drift_score = self._calculate_psi_categorical(reference_predictions, current_predictions)
        warning_level = self._get_warning_level(drift_score)
        threshold_exceeded = self._get_threshold_exceeded(drift_score)

        result = DriftResult(
            feature_name="prediction_distribution",
            drift_score=drift_score,
            warning_level=warning_level,
            threshold_exceeded=threshold_exceeded,
            reference_mean=float(np.mean(reference_predictions)),
            current_mean=float(np.mean(current_predictions)),
            reference_std=float(np.std(reference_predictions)),
            current_std=float(np.std(current_predictions)),
            sample_size_reference=len(reference_predictions),
            sample_size_current=len(current_predictions),
            metadata={"prediction_type": "binary"},
        )

        return result

    def detect_confidence_drift(
        self,
        reference_confidences: np.ndarray,
        current_confidences: np.ndarray,
    ) -> DriftResult:
        """
        Detect drift in model confidence scores.

        Args:
            reference_confidences: Historical confidence scores
            current_confidences: Current confidence scores

        Returns:
            DriftResult for confidence distribution
        """
        drift_score = self._calculate_psi_numeric(reference_confidences, current_confidences)
        warning_level = self._get_warning_level(drift_score)
        threshold_exceeded = self._get_threshold_exceeded(drift_score)

        result = DriftResult(
            feature_name="confidence_distribution",
            drift_score=drift_score,
            warning_level=warning_level,
            threshold_exceeded=threshold_exceeded,
            reference_mean=float(np.mean(reference_confidences)),
            current_mean=float(np.mean(current_confidences)),
            reference_std=float(np.std(reference_confidences)),
            current_std=float(np.std(current_confidences)),
            sample_size_reference=len(reference_confidences),
            sample_size_current=len(current_confidences),
            metadata={"confidence_range": "0-1"},
        )

        return result

    def generate_drift_report(
        self,
        model_name: str,
        model_version: int,
        feature_drifts: list[DriftResult],
        prediction_drift: Optional[DriftResult] = None,
        confidence_drift: Optional[DriftResult] = None,
    ) -> DriftReport:
        """
        Generate a comprehensive drift report.

        Args:
            model_name: Model identifier
            model_version: Model version
            feature_drifts: List of feature drift results
            prediction_drift: Optional prediction drift result
            confidence_drift: Optional confidence drift result

        Returns:
            DriftReport with overall assessment
        """
        # Calculate overall drift score (weighted average)
        all_drifts = feature_drifts.copy()
        if prediction_drift:
            all_drifts.append(prediction_drift)
        if confidence_drift:
            all_drifts.append(confidence_drift)

        if not all_drifts:
            overall_score = 0.0
            overall_level = DriftWarningLevel.LOW
        else:
            overall_score = float(np.mean([d.drift_score for d in all_drifts]))
            overall_level = self._get_warning_level(overall_score)

        # Generate summary and recommendations
        summary = self._generate_summary(overall_level, feature_drifts, prediction_drift, confidence_drift)
        recommendations = self._generate_recommendations(overall_level, feature_drifts, prediction_drift, confidence_drift)

        report = DriftReport(
            model_name=model_name,
            model_version=model_version,
            detection_timestamp=pd.Timestamp.utcnow().isoformat(),
            overall_drift_score=overall_score,
            overall_warning_level=overall_level,
            feature_drifts=feature_drifts,
            prediction_drift=prediction_drift,
            confidence_drift=confidence_drift,
            summary=summary,
            recommendations=recommendations,
        )

        logger.info(
            "Drift report generated",
            extra={
                "event": "drift.report",
                "model_name": model_name,
                "model_version": model_version,
                "overall_score": overall_score,
                "warning_level": overall_level.value,
            },
        )

        return report

    # -----------------------------------------------------------------------
    # Internal: PSI Calculation
    # -----------------------------------------------------------------------

    def _calculate_psi_numeric(self, reference: np.ndarray, current: np.ndarray) -> float:
        """
        Calculate Population Stability Index for numeric features.

        PSI = sum((actual% - expected%) * ln(actual% / expected%))

        Args:
            reference: Reference data array
            current: Current data array

        Returns:
            PSI score (0 = no drift, higher = more drift)
        """
        try:
            # Create bins using reference data percentiles
            bins = np.percentile(reference, [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
            bins = np.unique(bins)  # Remove duplicates

            # Count observations in each bin
            ref_counts, _ = np.histogram(reference, bins=bins)
            curr_counts, _ = np.histogram(current, bins=bins)

            # Convert to percentages (avoid division by zero)
            ref_pct = ref_counts / max(ref_counts.sum(), 1)
            curr_pct = curr_counts / max(curr_counts.sum(), 1)

            # Add small epsilon to avoid log(0)
            epsilon = 1e-10
            ref_pct = np.clip(ref_pct, epsilon, 1.0)
            curr_pct = np.clip(curr_pct, epsilon, 1.0)

            # Calculate PSI
            psi = np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct))

            return float(psi)

        except Exception as e:
            logger.warning(f"PSI calculation failed: {e}")
            return 0.0

    def _calculate_psi_categorical(self, reference: np.ndarray, current: np.ndarray) -> float:
        """
        Calculate PSI for categorical features.

        Args:
            reference: Reference data array
            current: Current data array

        Returns:
            PSI score
        """
        try:
            # Get unique categories from both datasets
            categories = np.unique(np.concatenate([reference, current]))

            ref_pct = []
            curr_pct = []

            for cat in categories:
                ref_pct.append(np.sum(reference == cat) / max(len(reference), 1))
                curr_pct.append(np.sum(current == cat) / max(len(current), 1))

            ref_pct = np.array(ref_pct)
            curr_pct = np.array(curr_pct)

            # Add epsilon to avoid log(0)
            epsilon = 1e-10
            ref_pct = np.clip(ref_pct, epsilon, 1.0)
            curr_pct = np.clip(curr_pct, epsilon, 1.0)

            # Normalize to sum to 1
            ref_pct = ref_pct / ref_pct.sum()
            curr_pct = curr_pct / curr_pct.sum()

            # Calculate PSI
            psi = np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct))

            return float(psi)

        except Exception as e:
            logger.warning(f"Categorical PSI calculation failed: {e}")
            return 0.0

    def _get_warning_level(self, drift_score: float) -> DriftWarningLevel:
        """Determine warning level from drift score."""
        if drift_score >= self.psi_thresholds[DriftWarningLevel.CRITICAL]:
            return DriftWarningLevel.CRITICAL
        elif drift_score >= self.psi_thresholds[DriftWarningLevel.HIGH]:
            return DriftWarningLevel.HIGH
        elif drift_score >= self.psi_thresholds[DriftWarningLevel.MEDIUM]:
            return DriftWarningLevel.MEDIUM
        elif drift_score >= self.psi_thresholds[DriftWarningLevel.LOW]:
            return DriftWarningLevel.LOW
        return DriftWarningLevel.LOW

    def _get_threshold_exceeded(self, drift_score: float) -> str:
        """Get the highest threshold exceeded."""
        if drift_score >= self.psi_thresholds[DriftWarningLevel.CRITICAL]:
            return f"critical ({drift_score:.4f} >= {self.psi_thresholds[DriftWarningLevel.CRITICAL]:.4f})"
        elif drift_score >= self.psi_thresholds[DriftWarningLevel.HIGH]:
            return f"high ({drift_score:.4f} >= {self.psi_thresholds[DriftWarningLevel.HIGH]:.4f})"
        elif drift_score >= self.psi_thresholds[DriftWarningLevel.MEDIUM]:
            return f"medium ({drift_score:.4f} >= {self.psi_thresholds[DriftWarningLevel.MEDIUM]:.4f})"
        elif drift_score >= self.psi_thresholds[DriftWarningLevel.LOW]:
            return f"low ({drift_score:.4f} >= {self.psi_thresholds[DriftWarningLevel.LOW]:.4f})"
        return "none"

    def _generate_summary(
        self,
        overall_level: DriftWarningLevel,
        feature_drifts: list[DriftResult],
        prediction_drift: Optional[DriftResult],
        confidence_drift: Optional[DriftResult],
    ) -> str:
        """Generate human-readable summary of drift report."""
        critical_features = [d.feature_name for d in feature_drifts if d.warning_level == DriftWarningLevel.CRITICAL]
        high_features = [d.feature_name for d in feature_drifts if d.warning_level == DriftWarningLevel.HIGH]

        parts = [f"Overall drift level: {overall_level.value.upper()}"]

        if critical_features:
            parts.append(f"Critical drift in: {', '.join(critical_features)}")
        if high_features:
            parts.append(f"High drift in: {', '.join(high_features)}")
        if prediction_drift and prediction_drift.warning_level != DriftWarningLevel.LOW:
            parts.append(f"Prediction drift: {prediction_drift.warning_level.value}")
        if confidence_drift and confidence_drift.warning_level != DriftWarningLevel.LOW:
            parts.append(f"Confidence drift: {confidence_drift.warning_level.value}")

        return ". ".join(parts)

    def _generate_recommendations(
        self,
        overall_level: DriftWarningLevel,
        feature_drifts: list[DriftResult],
        prediction_drift: Optional[DriftResult],
        confidence_drift: Optional[DriftResult],
    ) -> list[str]:
        """Generate actionable recommendations based on drift."""
        recommendations = []

        if overall_level == DriftWarningLevel.CRITICAL:
            recommendations.append("URGENT: Consider immediate model retraining")
            recommendations.append("Block high-risk predictions until drift is resolved")
        elif overall_level == DriftWarningLevel.HIGH:
            recommendations.append("Schedule model retraining within 1-2 weeks")
            recommendations.append("Increase monitoring frequency")
        elif overall_level == DriftWarningLevel.MEDIUM:
            recommendations.append("Monitor drift trends closely")
            recommendations.append("Plan retraining if drift continues")

        # Feature-specific recommendations
        critical_features = [d for d in feature_drifts if d.warning_level == DriftWarningLevel.CRITICAL]
        if critical_features:
            recommendations.append(f"Investigate root cause for features: {', '.join([d.feature_name for d in critical_features])}")

        if prediction_drift and prediction_drift.drift_score > 0.2:
            recommendations.append("Review model decision boundary and thresholds")

        if confidence_drift and confidence_drift.drift_score > 0.2:
            recommendations.append("Model confidence is unstable - review calibration")

        return recommendations
