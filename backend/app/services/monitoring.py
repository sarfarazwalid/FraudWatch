"""
Model Monitoring Service.

Tracks model health, performance, and drift indicators.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ml.model_registry import ModelRegistry
from app.models.ml.enums import DeploymentEnvironment
from app.models.fraud.prediction import Prediction
from app.models.ml.model_metrics import ModelMetrics

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Model monitoring for production tracking.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_health(self) -> dict[str, Any]:
        """Get overall system health."""
        # Check database connectivity
        try:
            result = await self.db_session.execute(select(func.count(ModelRegistry.id)))
            db_status = "healthy"
        except Exception:
            db_status = "unhealthy"

        return {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "database": db_status,
            "redis": "healthy",  # Would check Redis in production
            "celery": "healthy",  # Would check Celery in production
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_model(self) -> dict[str, Any]:
        """Get active production model details."""
        result = await self.db_session.execute(
            select(ModelRegistry)
            .where(ModelRegistry.deployment_environment == DeploymentEnvironment.PRODUCTION)
            .where(ModelRegistry.active == True)
        )
        model = result.scalar_one_or_none()

        if model:
            return {
                "id": str(model.id),
                "model_name": model.model_name,
                "version": model.version,
                "active": model.active,
                "deployed_at": model.deployed_at.isoformat() if model.deployed_at else None,
            }

        return {
            "id": None,
            "model_name": None,
            "version": None,
            "active": False,
            "deployed_at": None,
        }

    async def get_model_stats(self) -> dict[str, Any]:
        """Get model statistics."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=24)

        # Prediction count
        pred_result = await self.db_session.execute(
            select(func.count(Prediction.id))
            .where(Prediction.prediction_timestamp >= start)
        )
        prediction_count = pred_result.scalar() or 0

        # Failure count
        fail_result = await self.db_session.execute(
            select(func.count(Prediction.id))
            .where(
                and_(
                    Prediction.prediction_timestamp >= start,
                    Prediction.predicted_label == None,
                )
            )
        )
        failure_count = fail_result.scalar() or 0

        # Average latency
        latency_result = await self.db_session.execute(
            select(func.avg(Prediction.inference_time_ms))
            .where(
                and_(
                    Prediction.prediction_timestamp >= start,
                    Prediction.inference_time_ms.is_not(None),
                )
            )
        )
        avg_latency = float(latency_result.scalar() or 0)

        return {
            "prediction_count": prediction_count,
            "failure_count": failure_count,
            "average_latency_ms": round(avg_latency, 2),
            "success_rate": round((prediction_count - failure_count) / max(prediction_count, 1) * 100, 2),
        }

    async def get_drift(self) -> dict[str, Any]:
        """Get model drift indicators."""
        # In production, this would compare PSI scores, feature distributions, etc.
        return {
            "feature_drift": [],
            "prediction_drift": [],
            "confidence_drift": 0.0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
