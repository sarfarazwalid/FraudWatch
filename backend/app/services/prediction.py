"""
Fraud Prediction Service.

Provides ML-based fraud prediction with fallback scoring model.
Designed to be replaced with XGBoost/Isolation Forest later.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.fraud.prediction import Prediction
from app.models.fraud.prediction_explanation import PredictionExplanation
from app.models.fraud.enums import PredictionLabel, ExplanationMethod
from app.models.transaction.transaction import Transaction
from app.repositories.base import BaseRepository
from app.schemas.fraud import PredictionResponse, FeatureImportance

logger = logging.getLogger(__name__)


class PredictionService:
    """
    Service for fraud prediction using ML models with fallback scoring.

    Currently uses a weighted scoring model as fallback.
    Ready for XGBoost/Isolation Forest integration.
    """

    # Model version for fallback scoring
    FALLBACK_MODEL_VERSION = "fallback_scoring_v1"

    # Feature weights for fallback scoring
    WEIGHTS = {
        "amount": 0.25,
        "velocity": 0.25,
        "device": 0.20,
        "location": 0.15,
        "merchant": 0.15,
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BaseRepository(Prediction, session)

    async def predict_transaction_risk(
        self,
        transaction: Transaction,
        features: Dict[str, Any],
    ) -> PredictionResponse:
        """
        Predict fraud risk for a transaction.

        Uses ML model if available, falls back to weighted scoring.

        Args:
            transaction: The transaction to evaluate
            features: Extracted feature dictionary with keys:
                - amount_score: float (0-1)
                - velocity_score: float (0-1)
                - device_score: float (0-1)
                - location_score: float (0-1)
                - merchant_score: float (0-1)
                - user_average_amount: float (for rule engine)
                - recent_transaction_count: int
                - vpn_detected: bool
                - country_risk_high: bool

        Returns:
            PredictionResponse with risk score, prediction, confidence
        """
        # Calculate risk score using weighted fallback model
        risk_score = self._calculate_weighted_score(features)

        # Determine prediction label
        prediction = "fraud" if risk_score >= 0.5 else "legitimate"

        # Calculate confidence based on distance from threshold
        confidence = self._calculate_confidence(risk_score)

        # Calculate feature importance
        feature_importance = self._calculate_feature_importance(features)

        # Store prediction in database
        await self._store_prediction(
            transaction_id=transaction.id,
            risk_score=risk_score,
            prediction_label=prediction,
            confidence=confidence,
            feature_importance=feature_importance,
            features=features,
        )

        return PredictionResponse(
            risk_score=round(risk_score, 4),
            prediction=prediction,
            confidence=round(confidence, 4),
            model_version=self.FALLBACK_MODEL_VERSION,
            feature_importance=feature_importance,
        )

    def _calculate_weighted_score(self, features: Dict[str, Any]) -> float:
        """
        Calculate weighted risk score from features.

        Formula:
        risk_score = amount_score * 0.25 + velocity_score * 0.25 +
                     device_score * 0.20 + location_score * 0.15 +
                     merchant_score * 0.15
        """
        score = 0.0
        score += features.get("amount_score", 0.0) * self.WEIGHTS["amount"]
        score += features.get("velocity_score", 0.0) * self.WEIGHTS["velocity"]
        score += features.get("device_score", 0.0) * self.WEIGHTS["device"]
        score += features.get("location_score", 0.0) * self.WEIGHTS["location"]
        score += features.get("merchant_score", 0.0) * self.WEIGHTS["merchant"]

        return min(max(score, 0.0), 1.0)

    def _calculate_confidence(self, risk_score: float) -> float:
        """
        Calculate confidence based on distance from decision threshold (0.5).

        Higher confidence when score is far from threshold.
        """
        distance = abs(risk_score - 0.5)
        # Map distance 0-0.5 to confidence 0.5-0.99
        confidence = 0.5 + (distance * 0.98)
        return min(max(confidence, 0.5), 0.99)

    def _calculate_feature_importance(
        self, features: Dict[str, Any]
    ) -> FeatureImportance:
        """
        Calculate normalized feature importance for the prediction.

        Each feature's contribution is its score * weight, normalized.
        """
        raw_contributions = {
            "amount": features.get("amount_score", 0.0) * self.WEIGHTS["amount"],
            "velocity": features.get("velocity_score", 0.0) * self.WEIGHTS["velocity"],
            "device": features.get("device_score", 0.0) * self.WEIGHTS["device"],
            "location": features.get("location_score", 0.0) * self.WEIGHTS["location"],
            "merchant": features.get("merchant_score", 0.0) * self.WEIGHTS["merchant"],
        }

        total = sum(raw_contributions.values())
        if total == 0:
            return FeatureImportance()

        return FeatureImportance(
            amount=round(raw_contributions["amount"] / total, 4),
            velocity=round(raw_contributions["velocity"] / total, 4),
            device=round(raw_contributions["device"] / total, 4),
            location=round(raw_contributions["location"] / total, 4),
            merchant=round(raw_contributions["merchant"] / total, 4),
        )

    async def _store_prediction(
        self,
        transaction_id: UUID,
        risk_score: float,
        prediction_label: str,
        confidence: float,
        feature_importance: FeatureImportance,
        features: Dict[str, Any],
    ) -> Prediction:
        """Store prediction record in database."""
        prediction = Prediction(
            transaction_id=transaction_id,
            model_version_id=self.FALLBACK_MODEL_VERSION,
            predicted_label=PredictionLabel(prediction_label),
            confidence_score=confidence,
            probability_score=risk_score,
            inference_time_ms=0,
            prediction_timestamp=datetime.now(timezone.utc),
        )
        self.session.add(prediction)
        await self.session.flush()
        await self.session.refresh(prediction)

        # Store feature importance as explanations
        explanations_data = [
            ("amount", str(features.get("amount_score", 0)), feature_importance.amount, 1),
            ("velocity", str(features.get("velocity_score", 0)), feature_importance.velocity, 2),
            ("device", str(features.get("device_score", 0)), feature_importance.device, 3),
            ("location", str(features.get("location_score", 0)), feature_importance.location, 4),
            ("merchant", str(features.get("merchant_score", 0)), feature_importance.merchant, 5),
        ]

        for feature_name, feature_value, importance, order in explanations_data:
            explanation = PredictionExplanation(
                prediction_id=prediction.id,
                explanation_method=ExplanationMethod.FEATURE_IMPORTANCE,
                feature_name=feature_name,
                feature_value=feature_value,
                importance_score=importance,
                contribution_direction="positive" if importance > 0 else "negative",
                display_order=order,
            )
            self.session.add(explanation)

        await self.session.flush()
        return prediction

    async def get_prediction(self, prediction_id: str) -> Optional[Prediction]:
        """Get prediction by ID."""
        return await self.repo.get(prediction_id)

    async def get_prediction_by_transaction(
        self, transaction_id: str
    ) -> Optional[Prediction]:
        """Get prediction for a transaction."""
        result = await self.session.execute(
            select(Prediction).where(
                Prediction.transaction_id == transaction_id
            ).order_by(Prediction.prediction_timestamp.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_transaction_velocity_features(
        self, sender_identifier: str, minutes: int = 5
    ) -> Tuple[int, float]:
        """
        Calculate velocity features for a sender.

        Args:
            sender_identifier: Sender account/identifier
            minutes: Time window in minutes

        Returns:
            Tuple of (transaction_count, frequency_score)
        """
        since = datetime.now(timezone.utc) - __import__("datetime").timedelta(minutes=minutes)

        result = await self.session.execute(
            select(func.count(Transaction.id)).where(
                and_(
                    Transaction.sender_identifier == sender_identifier,
                    Transaction.transaction_timestamp >= since,
                )
            )
        )
        count = result.scalar() or 0

        # Frequency score: 0 for 0-3 txns, increases after
        if count <= 3:
            frequency_score = 0.0
        elif count <= 5:
            frequency_score = 0.3
        elif count <= 10:
            frequency_score = 0.6
        else:
            frequency_score = 1.0

        return count, frequency_score

    async def get_user_average_amount(
        self, sender_identifier: str
    ) -> float:
        """Get average transaction amount for a sender."""
        result = await self.session.execute(
            select(func.avg(Transaction.amount)).where(
                Transaction.sender_identifier == sender_identifier
            )
        )
        avg = result.scalar()
        return float(avg) if avg else 0.0
