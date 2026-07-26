"""
Explainability Service.

Provides human-readable explanations for fraud predictions.
Prepared for future SHAP integration.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.fraud.prediction import Prediction
from app.models.fraud.prediction_explanation import PredictionExplanation
from app.models.fraud.enums import ExplanationMethod
from app.schemas.fraud import ExplanationResponse, FeatureImportance

logger = logging.getLogger(__name__)


class ExplainabilityService:
    """
    Service for generating human-readable explanations of fraud predictions.

    Currently uses rule-based explanations from feature importance.
    Prepared for future SHAP/LIME integration.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_explanation(
        self, transaction_id: str
    ) -> Optional[ExplanationResponse]:
        """
        Get a human-readable explanation for a transaction's fraud prediction.

        Args:
            transaction_id: The transaction UUID

        Returns:
            ExplanationResponse with reasons and feature importance, or None
        """
        # Get the latest prediction for this transaction
        result = await self.session.execute(
            select(Prediction)
            .where(Prediction.transaction_id == transaction_id)
            .order_by(Prediction.prediction_timestamp.desc())
            .limit(1)
        )
        prediction = result.scalar_one_or_none()

        if not prediction:
            return None

        # Get explanations from database
        explanations_result = await self.session.execute(
            select(PredictionExplanation)
            .where(PredictionExplanation.prediction_id == prediction.id)
            .order_by(PredictionExplanation.display_order.asc())
        )
        explanations = list(explanations_result.scalars().all())

        # Build feature importance
        feature_importance = FeatureImportance()
        for exp in explanations:
            importance = float(exp.importance_score) if exp.importance_score else 0.0
            if exp.feature_name == "amount":
                feature_importance.amount = importance
            elif exp.feature_name == "velocity":
                feature_importance.velocity = importance
            elif exp.feature_name == "device":
                feature_importance.device = importance
            elif exp.feature_name == "location":
                feature_importance.location = importance
            elif exp.feature_name == "merchant":
                feature_importance.merchant = importance

        # Generate human-readable reasons
        reasons = self._generate_reasons(
            prediction=prediction,
            explanations=explanations,
            feature_importance=feature_importance,
        )

        # Determine decision
        risk_score = float(prediction.probability_score) if prediction.probability_score else 0.0
        decision = self._determine_decision(risk_score)

        return ExplanationResponse(
            transaction_id=str(transaction_id),
            risk_score=risk_score,
            decision=decision,
            reasons=reasons,
            feature_importance=feature_importance,
        )

    def _generate_reasons(
        self,
        prediction: Prediction,
        explanations: List[PredictionExplanation],
        feature_importance: FeatureImportance,
    ) -> List[str]:
        """
        Generate human-readable reasons for the prediction.

        Uses feature importance to determine which factors contributed most.
        """
        reasons: List[str] = []

        # Sort explanations by importance (descending)
        sorted_exps = sorted(
            explanations,
            key=lambda e: float(e.importance_score) if e.importance_score else 0,
            reverse=True,
        )

        # Generate reason for each significant feature
        for exp in sorted_exps:
            importance = float(exp.importance_score) if exp.importance_score else 0.0
            if importance < 0.1:
                continue

            if exp.feature_name == "amount":
                reasons.append("Transaction amount unusually high")
            elif exp.feature_name == "velocity":
                reasons.append("High transaction velocity detected")
            elif exp.feature_name == "device":
                reasons.append("New or untrusted device detected")
            elif exp.feature_name == "location":
                reasons.append("Suspicious location detected")
            elif exp.feature_name == "merchant":
                reasons.append("High-risk merchant involved")

        # Add prediction-based reasons
        if prediction.predicted_label.value == "fraud":
            reasons.append("ML model classified as fraudulent")
        elif prediction.predicted_label.value == "suspicious":
            reasons.append("ML model flagged as suspicious")

        # If no specific reasons, provide generic one
        if not reasons:
            risk_score = float(prediction.probability_score) if prediction.probability_score else 0.0
            if risk_score >= 0.5:
                reasons.append("Multiple risk factors detected")
            else:
                reasons.append("Transaction appears normal")

        return reasons

    def _determine_decision(self, risk_score: float) -> str:
        """Determine the final decision based on risk score."""
        if risk_score >= 0.85:
            return "reject"
        elif risk_score >= 0.7:
            return "review"
        elif risk_score >= 0.5:
            return "review"
        else:
            return "approve"

    async def get_feature_importance(
        self, transaction_id: str
    ) -> Optional[FeatureImportance]:
        """Get feature importance for a transaction's prediction."""
        result = await self.session.execute(
            select(Prediction)
            .where(Prediction.transaction_id == transaction_id)
            .order_by(Prediction.prediction_timestamp.desc())
            .limit(1)
        )
        prediction = result.scalar_one_or_none()

        if not prediction:
            return None

        explanations_result = await self.session.execute(
            select(PredictionExplanation)
            .where(PredictionExplanation.prediction_id == prediction.id)
        )
        explanations = list(explanations_result.scalars().all())

        fi = FeatureImportance()
        for exp in explanations:
            importance = float(exp.importance_score) if exp.importance_score else 0.0
            if exp.feature_name == "amount":
                fi.amount = importance
            elif exp.feature_name == "velocity":
                fi.velocity = importance
            elif exp.feature_name == "device":
                fi.device = importance
            elif exp.feature_name == "location":
                fi.location = importance
            elif exp.feature_name == "merchant":
                fi.merchant = importance

        return fi
