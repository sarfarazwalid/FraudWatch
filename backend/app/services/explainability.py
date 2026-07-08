"""
Prediction Explainability Service.

Provides human-readable explanations for fraud predictions using
feature importance, rule results, and SHAP integration when available.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fraud.prediction import Prediction
from app.models.fraud.prediction_explanation import PredictionExplanation
from app.models.fraud.enums import ExplanationMethod
from app.models.fraud.prediction_explanation import PredictionExplanation

logger = logging.getLogger(__name__)


class ExplainabilityService:
    """
    Generates explanations for ML predictions.

    Supports multiple explanation methods:
    - Feature importance ranking
    - Rule-based explanations
    - SHAP integration (if available)
    - Human-readable text generation
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_prediction_details(self, prediction_id: UUID) -> Optional[dict[str, Any]]:
        """
        Retrieve full prediction details with explanations.

        Args:
            prediction_id: Prediction UUID

        Returns:
            Dict with prediction details or None if not found
        """
        result = await self.db_session.execute(
            select(Prediction).where(Prediction.id == prediction_id)
        )
        prediction = result.scalar_one_or_none()
        if not prediction:
            return None

        return {
            "id": str(prediction.id),
            "transaction_id": str(prediction.transaction_id),
            "model_version_id": prediction.model_version_id,
            "predicted_label": prediction.predicted_label.value if prediction.predicted_label else None,
            "confidence_score": float(prediction.confidence_score) if prediction.confidence_score else None,
            "probability_score": float(prediction.probability_score) if prediction.probability_score else None,
            "inference_time_ms": prediction.inference_time_ms,
            "prediction_timestamp": prediction.prediction_timestamp.isoformat() if prediction.prediction_timestamp else None,
        }

    async def get_feature_snapshot(self, prediction_id: UUID) -> list[dict[str, Any]]:
        """
        Retrieve feature snapshot for a prediction.

        Args:
            prediction_id: Prediction UUID

        Returns:
            List of feature explanations
        """
        result = await self.db_session.execute(
            select(PredictionExplanation)
            .where(PredictionExplanation.prediction_id == prediction_id)
            .order_by(PredictionExplanation.display_order.asc())
        )
        explanations = result.scalars().all()

        return [
            {
                "feature_name": exp.feature_name,
                "feature_value": exp.feature_value,
                "importance_score": float(exp.importance_score) if exp.importance_score else None,
                "contribution_direction": exp.contribution_direction,
                "explanation_method": exp.explanation_method.value if exp.explanation_method else "rule",
            }
            for exp in explanations
        ]

    async def get_rule_results(self, prediction_id: UUID) -> list[dict[str, Any]]:
        """
        Retrieve rule results for a prediction.

        Rules are stored as PredictionExplanation records with explanation_method=RULE.

        Args:
            prediction_id: Prediction UUID

        Returns:
            List of rule evaluation results
        """
        result = await self.db_session.execute(
            select(PredictionExplanation)
            .where(
                PredictionExplanation.prediction_id == prediction_id,
                PredictionExplanation.explanation_method == ExplanationMethod.RULE_EXPLANATION,
            )
            .order_by(PredictionExplanation.display_order.asc())
        )
        rules = result.scalars().all()

        return [
            {
                "rule_name": exp.feature_name,
                "rule_value": exp.feature_value,
                "score": float(exp.importance_score) if exp.importance_score else None,
                "severity": exp.contribution_direction,
            }
            for exp in rules
        ]

    async def generate_explanation(self, prediction_id: UUID) -> dict[str, Any]:
        """
        Generate a comprehensive human-readable explanation.

        Args:
            prediction_id: Prediction UUID

        Returns:
            Complete explanation payload
        """
        prediction = await self.get_prediction_details(prediction_id)
        if not prediction:
            return {"error": "Prediction not found"}

        features = await self.get_feature_snapshot(prediction_id)
        rules = await self.get_rule_results(prediction_id)

        feature_importance = self._calculate_feature_importance(features)
        human_readable = self._build_human_readable(
            prediction, features, rules, feature_importance
        )

        return {
            "prediction": prediction,
            "explanation": {
                "summary": human_readable,
                "top_features": feature_importance[:5],
                "feature_count": len(features),
                "rule_count": len(rules),
                "methods_used": self._get_methods_used(features),
            },
            "features": features,
            "rules": rules,
        }

    def _calculate_feature_importance(
        self, features: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Rank features by importance score.

        Args:
            features: List of feature explanations

        Returns:
            Features sorted by importance (descending)
        """
        ranked = [
            {
                "feature_name": f["feature_name"],
                "importance_score": f["importance_score"] or 0,
                "contribution_direction": f["contribution_direction"],
            }
            for f in features
            if f.get("importance_score") is not None
        ]
        return sorted(ranked, key=lambda x: x["importance_score"], reverse=True)

    def _build_human_readable(
        self,
        prediction: dict[str, Any],
        features: list[dict[str, Any]],
        rules: list[dict[str, Any]],
        feature_importance: list[dict[str, Any]],
    ) -> str:
        """
        Build a human-readable explanation string.

        Args:
            prediction: Prediction details
            features: Feature explanations
            rules: Rule results
            feature_importance: Ranked feature importance

        Returns:
            Human-readable explanation text
        """
        label = prediction.get("predicted_label", "unknown")
        confidence = prediction.get("confidence_score", 0)
        top_features = feature_importance[:3] if feature_importance else []
        triggered_rules = [r for r in rules if r.get("score") and r["score"] > 0]

        parts = [
            f"This transaction was classified as '{label}' "
            f"with a confidence score of {confidence:.2%}."
        ]

        if top_features:
            feature_descriptions = [
                f"'{f['feature_name']}' contributed {f['contribution_direction'] or 'neutrally'}"
                for f in top_features
            ]
            parts.append(
                f"The most influential features were: {'; '.join(feature_descriptions)}."
            )

        if triggered_rules:
            parts.append(
                f"{len(triggered_rules)} fraud detection rules were triggered."
            )

        return " ".join(parts)

    def _get_methods_used(self, features: list[dict[str, Any]]) -> list[str]:
        """Get the list of explanation methods used."""
        methods = set()
        for f in features:
            method = f.get("explanation_method")
            if method:
                methods.add(method)
        return sorted(methods)

    async def generate_fallback_explanation(
        self, prediction_id: UUID
    ) -> dict[str, Any]:
        """
        Generate a fallback explanation when SHAP/XAI data is unavailable.

        Args:
            prediction_id: Prediction UUID

        Returns:
            Simplified explanation payload
        """
        prediction = await self.get_prediction_details(prediction_id)
        if not prediction:
            return {"error": "Prediction not found"}

        return {
            "prediction": prediction,
            "explanation": {
                "summary": (
                    f"Prediction based on ML model '{prediction.get('model_version_id', 'unknown')}'. "
                    f"Detailed feature importance is not available for this prediction."
                ),
                "top_features": [],
                "feature_count": 0,
                "rule_count": 0,
                "methods_used": ["model_output"],
            },
            "features": [],
            "rules": [],
        }
