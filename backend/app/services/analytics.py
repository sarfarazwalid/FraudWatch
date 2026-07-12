"""
Analytics Engine Service.

Provides real database queries for fraud analytics, operations metrics, and model performance.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fraud.prediction import Prediction
from app.models.fraud.enums import PredictionLabel
from app.models.transaction.transaction import Transaction
from app.models.fraud.fraud_case import FraudCase
from app.models.transaction.merchant import Merchant
from app.models.transaction.device import Device
from app.models.ml.model_metrics import ModelMetrics

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Analytics engine providing real-time and historical fraud metrics.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_fraud_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Get fraud detection metrics."""
        now = datetime.now(timezone.utc)
        start = start_date or (now - timedelta(hours=24))
        end = end_date or now

        # Total transactions
        total_result = await self.db_session.execute(
            select(func.count(Transaction.id)).where(
                and_(
                    Transaction.created_at >= start,
                    Transaction.created_at <= end,
                )
            )
        )
        total_transactions = total_result.scalar() or 0

        # Fraud predictions
        fraud_result = await self.db_session.execute(
            select(func.count(Prediction.id)).where(
                and_(
                    Prediction.prediction_timestamp >= start,
                    Prediction.prediction_timestamp <= end,
                    Prediction.predicted_label == PredictionLabel.FRAUD,
                )
            )
        )
        fraud_count = fraud_result.scalar() or 0

        # Suspicious predictions
        suspicious_result = await self.db_session.execute(
            select(func.count(Prediction.id)).where(
                and_(
                    Prediction.prediction_timestamp >= start,
                    Prediction.prediction_timestamp <= end,
                    Prediction.predicted_label == PredictionLabel.SUSPICIOUS,
                )
            )
        )
        suspicious_count = suspicious_result.scalar() or 0

        fraud_rate = (fraud_count / total_transactions * 100) if total_transactions > 0 else 0

        # Period comparison
        prev_start = start - (end - start)
        prev_end = start
        prev_fraud_result = await self.db_session.execute(
            select(func.count(Prediction.id)).where(
                and_(
                    Prediction.prediction_timestamp >= prev_start,
                    Prediction.prediction_timestamp <= prev_end,
                    Prediction.predicted_label == PredictionLabel.FRAUD,
                )
            )
        )
        prev_fraud_count = prev_fraud_result.scalar() or 0
        trending_up = fraud_count > prev_fraud_count
        period_comparison = ((fraud_count - prev_fraud_count) / max(prev_fraud_count, 1) * 100) if prev_fraud_count > 0 else None

        return {
            "fraud_rate": round(fraud_rate, 2),
            "fraud_volume": fraud_count,
            "suspicious_volume": suspicious_count,
            "total_transactions": total_transactions,
            "trending_up": trending_up,
            "period_comparison": round(period_comparison, 2) if period_comparison else None,
        }

    async def get_fraud_by_merchant(
        self,
        start_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get fraud distribution by merchant."""
        now = datetime.now(timezone.utc)
        start = start_date or (now - timedelta(days=30))

        result = await self.db_session.execute(
            select(
                Merchant.merchant_name.label("dimension"),
                func.count(Prediction.id).label("fraud_count"),
            )
            .select_from(Transaction)
            .join(Prediction, Transaction.id == Prediction.transaction_id)
            .join(Merchant, Transaction.merchant_id == Merchant.id)
            .where(
                and_(
                    Prediction.prediction_timestamp >= start,
                    Prediction.predicted_label == PredictionLabel.FRAUD,
                )
            )
            .group_by(Merchant.merchant_name)
            .order_by(func.count(Prediction.id).desc())
            .limit(limit)
        )

        return [
            {
                "dimension": row.dimension or "Unknown",
                "fraud_count": row.fraud_count,
            }
            for row in result.fetchall()
        ]

    async def get_fraud_by_device(
        self,
        start_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get fraud distribution by device."""
        now = datetime.now(timezone.utc)
        start = start_date or (now - timedelta(days=30))

        result = await self.db_session.execute(
            select(
                Device.device_fingerprint.label("dimension"),
                func.count(Prediction.id).label("fraud_count"),
            )
            .select_from(Transaction)
            .join(Prediction, Transaction.id == Prediction.transaction_id)
            .join(Device, Transaction.device_id == Device.id)
            .where(
                and_(
                    Prediction.prediction_timestamp >= start,
                    Prediction.predicted_label == PredictionLabel.FRAUD,
                )
            )
            .group_by(Device.device_fingerprint)
            .order_by(func.count(Prediction.id).desc())
            .limit(limit)
        )

        return [
            {
                "dimension": row.dimension or "Unknown",
                "fraud_count": row.fraud_count,
            }
            for row in result.fetchall()
        ]

    async def get_fraud_trends(
        self,
        start_date: Optional[datetime] = None,
        period: str = "24h",
    ) -> list[dict[str, Any]]:
        """Get fraud trends over time."""
        now = datetime.now(timezone.utc)
        start = start_date or (now - timedelta(days=7))

        result = await self.db_session.execute(
            select(
                func.date_trunc("hour", Prediction.prediction_timestamp).label("timestamp"),
                func.count(Prediction.id).label("value"),
            )
            .where(
                and_(
                    Prediction.prediction_timestamp >= start,
                    Prediction.predicted_label == PredictionLabel.FRAUD,
                )
            )
            .group_by(func.date_trunc("hour", Prediction.prediction_timestamp))
            .order_by("timestamp")
        )

        return [
            {
                "timestamp": row.timestamp.isoformat(),
                "value": float(row.value),
            }
            for row in result.fetchall()
        ]

    async def get_operations_metrics(
        self,
        start_date: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Get operations performance metrics."""
        now = datetime.now(timezone.utc)
        start = start_date or (now - timedelta(hours=24))

        pred_result = await self.db_session.execute(
            select(func.count(Prediction.id)).where(
                Prediction.prediction_timestamp >= start
            )
        )
        prediction_volume = pred_result.scalar() or 0

        latency_result = await self.db_session.execute(
            select(func.avg(Prediction.inference_time_ms)).where(
                Prediction.inference_time_ms.is_not(None),
                Prediction.prediction_timestamp >= start,
            )
        )
        prediction_latency_avg_ms = float(latency_result.scalar() or 0)

        return {
            "prediction_volume": prediction_volume,
            "prediction_latency_avg_ms": round(prediction_latency_avg_ms, 2),
        }

    async def get_model_performance_metrics(
        self,
        model_version_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get model performance metrics."""
        result = await self.db_session.execute(
            select(ModelMetrics)
            .where(
                ModelMetrics.model_version_id == (model_version_id or "v1.0.0")
            )
            .order_by(ModelMetrics.created_at.desc())
            .limit(1)
        )
        metrics = result.scalar_one_or_none()

        if metrics:
            return {
                "accuracy": float(metrics.accuracy) if metrics.accuracy else None,
                "precision": float(metrics.precision) if metrics.precision else None,
                "recall": float(metrics.recall) if metrics.recall else None,
                "f1_score": float(metrics.f1_score) if metrics.f1_score else None,
                "roc_auc": float(metrics.roc_auc) if metrics.roc_auc else None,
            }

        return {
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "roc_auc": None,
        }

    async def get_all_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Get all analytics data."""
        fraud_metrics = await self.get_fraud_metrics(start_date, end_date)
        fraud_by_merchant = await self.get_fraud_by_merchant(start_date)
        fraud_by_device = await self.get_fraud_by_device(start_date)
        fraud_trends = await self.get_fraud_trends(start_date)
        operations_metrics = await self.get_operations_metrics(start_date)
        model_metrics = await self.get_model_performance_metrics()

        return {
            "fraud_metrics": fraud_metrics,
            "fraud_by_merchant": fraud_by_merchant,
            "fraud_by_device": fraud_by_device,
            "fraud_trends": fraud_trends,
            "operations_metrics": operations_metrics,
            "model_metrics": model_metrics,
        }
