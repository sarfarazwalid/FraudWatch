"""
Model Monitoring Service for ML Model Performance Tracking.

Tracks:
- Prediction latency
- Throughput
- Confidence histogram
- Prediction distribution
- Fraud ratio
- CPU/memory usage
- Model uptime
- Daily/weekly requests
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np
import psutil

logger = logging.getLogger(__name__)


@dataclass
class PredictionMetrics:
    """Metrics for a single prediction."""
    latency_ms: float
    confidence: float
    prediction: int
    timestamp: datetime
    model_version_id: str
    transaction_id: str


@dataclass
class ModelHealthMetrics:
    """Overall model health and performance metrics."""
    model_name: str
    model_version: int
    uptime_seconds: float
    total_predictions: int
    predictions_per_second: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    avg_confidence: float
    confidence_std: float
    fraud_ratio: float
    cpu_usage_percent: float
    memory_usage_mb: float
    daily_requests: int
    weekly_requests: int
    last_prediction_at: Optional[datetime]
    error_count: int
    error_rate: float


class ModelMonitor:
    """
    Real-time model performance monitoring.

    Tracks prediction metrics, system resources, and model health.
    """

    def __init__(self, model_name: str, model_version: int, window_size: int = 1000):
        """
        Initialize model monitor.

        Args:
            model_name: Model identifier
            model_version: Model version number
            window_size: Number of recent predictions to keep in memory
        """
        self.model_name = model_name
        self.model_version = model_version
        self.window_size = window_size

        # Prediction history (circular buffer)
        self._predictions: list[PredictionMetrics] = []
        self._total_predictions = 0
        self._error_count = 0
        self._start_time = time.time()

        # Daily/weekly counters
        self._daily_requests = 0
        self._weekly_requests = 0
        self._last_day = datetime.now(timezone.utc).day
        self._last_week = datetime.now(timezone.utc).isocalendar().week

    def record_prediction(
        self,
        latency_ms: float,
        confidence: float,
        prediction: int,
        transaction_id: str,
    ) -> None:
        """
        Record a prediction event.

        Args:
            latency_ms: Inference latency in milliseconds
            confidence: Model confidence score
            prediction: Predicted class (0 or 1)
            transaction_id: Transaction UUID
        """
        now = datetime.now(timezone.utc)

        # Update daily/weekly counters
        current_day = now.day
        current_week = now.isocalendar().week
        if current_day != self._last_day:
            self._daily_requests = 0
            self._last_day = current_day
        if current_week != self._last_week:
            self._weekly_requests = 0
            self._last_week = current_week

        self._daily_requests += 1
        self._weekly_requests += 1
        self._total_predictions += 1

        # Add to circular buffer
        metric = PredictionMetrics(
            latency_ms=latency_ms,
            confidence=confidence,
            prediction=prediction,
            timestamp=now,
            model_version_id=f"{self.model_name}:{self.model_version}",
            transaction_id=transaction_id,
        )
        self._predictions.append(metric)

        # Trim to window size
        if len(self._predictions) > self.window_size:
            self._predictions = self._predictions[-self.window_size:]

    def record_error(self) -> None:
        """Record a prediction error."""
        self._error_count += 1

    def get_health_metrics(self) -> ModelHealthMetrics:
        """
        Get current model health metrics.

        Returns:
            ModelHealthMetrics with current performance data
        """
        uptime = time.time() - self._start_time

        # Calculate metrics from recent predictions
        if self._predictions:
            latencies = [p.latency_ms for p in self._predictions]
            confidences = [p.confidence for p in self._predictions]
            predictions = [p.prediction for p in self._predictions]

            avg_latency = float(np.mean(latencies))
            p95_latency = float(np.percentile(latencies, 95))
            p99_latency = float(np.percentile(latencies, 99))
            avg_confidence = float(np.mean(confidences))
            confidence_std = float(np.std(confidences))
            fraud_ratio = float(np.mean(predictions))
        else:
            avg_latency = 0.0
            p95_latency = 0.0
            p99_latency = 0.0
            avg_confidence = 0.0
            confidence_std = 0.0
            fraud_ratio = 0.0

        # Calculate throughput
        if uptime > 0:
            throughput = self._total_predictions / uptime
        else:
            throughput = 0.0

        # Get system metrics
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Calculate error rate
        error_rate = self._error_count / max(self._total_predictions, 1)

        # Last prediction time
        last_pred = self._predictions[-1].timestamp if self._predictions else None

        return ModelHealthMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            uptime_seconds=uptime,
            total_predictions=self._total_predictions,
            predictions_per_second=throughput,
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            avg_confidence=avg_confidence,
            confidence_std=confidence_std,
            fraud_ratio=fraud_ratio,
            cpu_usage_percent=cpu_usage,
            memory_usage_mb=memory_usage,
            daily_requests=self._daily_requests,
            weekly_requests=self._weekly_requests,
            last_prediction_at=last_pred,
            error_count=self._error_count,
            error_rate=error_rate,
        )

    def get_prediction_distribution(self) -> dict[str, Any]:
        """
        Get prediction distribution statistics.

        Returns:
            Dictionary with prediction distribution
        """
        if not self._predictions:
            return {"fraud": 0, "legitimate": 0, "total": 0}

        predictions = [p.prediction for p in self._predictions]
        fraud_count = sum(predictions)
        legitimate_count = len(predictions) - fraud_count

        return {
            "fraud": fraud_count,
            "legitimate": legitimate_count,
            "total": len(predictions),
            "fraud_ratio": fraud_count / len(predictions),
        }

    def get_confidence_histogram(self, bins: int = 10) -> dict[str, list[float]]:
        """
        Get confidence score histogram.

        Args:
            bins: Number of histogram bins

        Returns:
            Dictionary with bin edges and counts
        """
        if not self._predictions:
            return {"bins": [], "counts": []}

        confidences = [p.confidence for p in self._predictions]
        counts, bin_edges = np.histogram(confidences, bins=bins, range=(0, 1))

        return {
            "bins": bin_edges.tolist(),
            "counts": counts.tolist(),
        }

    def get_latency_percentiles(self) -> dict[str, float]:
        """
        Get latency percentiles.

        Returns:
            Dictionary with latency percentiles
        """
        if not self._predictions:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}

        latencies = [p.latency_ms for p in self._predictions]

        return {
            "p50": float(np.percentile(latencies, 50)),
            "p95": float(np.percentile(latencies, 95)),
            "p99": float(np.percentile(latencies, 99)),
            "max": float(np.max(latencies)),
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._predictions.clear()
        self._total_predictions = 0
        self._error_count = 0
        self._start_time = time.time()
        self._daily_requests = 0
        self._weekly_requests = 0
