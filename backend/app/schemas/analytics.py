"""
Analytics Pydantic Schemas.

Define request/response schemas for analytics endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TimeSeriesPoint(BaseModel):
    """Single point in a time series."""
    timestamp: datetime
    value: float


class FraudMetrics(BaseModel):
    """Fraud detection metrics."""
    fraud_rate: float = Field(ge=0, le=100, description="Fraud rate percentage")
    fraud_volume: int = Field(ge=0, description="Number of fraudulent transactions")
    total_transactions: int = Field(ge=0, description="Total transaction count")
    trending_up: bool = Field(default=False, description="Whether fraud is trending up")
    period_comparison: Optional[float] = Field(default=None, description="Comparison to previous period")


class FraudByDimension(BaseModel):
    """Fraud metrics grouped by a dimension."""
    dimension: str
    fraud_count: int
    total_count: int
    fraud_rate: float


class OperationsMetrics(BaseModel):
    """Operations performance metrics."""
    prediction_volume: int = Field(ge=0, description="Total predictions made")
    prediction_latency_avg_ms: float = Field(ge=0, description="Average prediction latency")
    alert_generation_latency_avg_ms: float = Field(ge=0, description="Average alert generation latency")
    investigation_resolution_avg_hours: float = Field(ge=0, description="Average investigation resolution time")


class ModelPerformanceMetrics(BaseModel):
    """Model performance metrics."""
    accuracy: Optional[float] = Field(ge=0, le=100, description="Model accuracy percentage")
    precision: Optional[float] = Field(ge=0, le=100, description="Precision score")
    recall: Optional[float] = Field(ge=0, le=100, description="Recall score")
    f1_score: Optional[float] = Field(ge=0, le=100, description="F1 score")
    roc_auc: Optional[float] = Field(ge=0, le=100, description="ROC-AUC score")
    pr_auc: Optional[float] = Field(ge=0, le=100, description="PR-AUC score")
    confidence_distribution: Optional[list[TimeSeriesPoint]] = None


class AnalyticsTimeRange(BaseModel):
    """Time range for analytics queries."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    period: Optional[str] = Field(default="24h", pattern="^(24h|7d|30d|90d|1y)$")


class ChartDataPoint(BaseModel):
    """Generic chart data point."""
    name: str
    value: float
    extra: Optional[dict[str, Any]] = None


class AnalyticsResponse(BaseModel):
    """Combined analytics response."""
    fraud_metrics: FraudMetrics
    fraud_by_merchant: list[FraudByDimension]
    fraud_by_device: list[FraudByDimension]
    fraud_by_payment_method: list[FraudByDimension]
    fraud_by_transaction_type: list[FraudByDimension]
    fraud_by_location: list[FraudByDimension]
    operations_metrics: OperationsMetrics
    model_metrics: ModelPerformanceMetrics
