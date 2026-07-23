"""
Prediction Service - Core fraud detection orchestration.

This service coordinates the complete prediction pipeline:
1. Feature extraction
2. ML model inference
3. Rule engine evaluation
4. Score combination
5. Risk assessment
6. Alert generation
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fraud.prediction import Prediction
from app.models.fraud.prediction_explanation import PredictionExplanation
from app.models.fraud.fraud_alert import FraudAlert
from app.models.transaction.risk_level import RiskLevelCode
from app.models.transaction.transaction import Transaction
from app.repositories.transaction import TransactionRepository
from app.repositories.fraud_alert import FraudAlertRepository
from app.repositories.model_registry import ModelRegistryRepository
from sqlalchemy import select

# ML imports will be loaded lazily to avoid import errors at startup
FeatureExtractor = None
load_all_rules = None
RuleResult = None
RuleSeverity = None
BaseMLModel = None

# Enums
from app.models.fraud.enums import PredictionLabel


class PredictionService:
    """
    Orchestrates fraud prediction pipeline.

    Coordinates feature extraction, ML inference, and rule evaluation
    to produce comprehensive fraud risk assessments.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialize prediction service.

        Args:
            db_session: SQLAlchemy async session
        """
        self.db_session = db_session
        self.transaction_repo = TransactionRepository(db_session)
        self.alert_repo = FraudAlertRepository(db_session)
        self.model_repo = ModelRegistryRepository(db_session)

        # Initialize components lazily to avoid import errors at startup
        self.feature_extractor = None
        self.rule_registry = None
        self.rule_engine = None
        self.ml_model = None

    def _load_production_model(self) -> None:
        """Load the current production ML model."""
        # In production, load from model registry
        # For now, use placeholder
        self.ml_model = None

    async def predict_transaction(self, transaction_id: UUID) -> Prediction | None:
        """
        Run complete fraud prediction on a transaction.

        Args:
            transaction_id: Transaction UUID

        Returns:
            Prediction record with results
        """
        # Step 1: Load transaction
        transaction = await self.transaction_repo.get(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        # Step 2: Extract features
        feature_vector = self.feature_extractor.extract_all(str(transaction_id))
        features = feature_vector.features

        # Step 3: Run ML model (placeholder - returns 0 if no model)
        ml_score = self._run_ml_model(features)

        # Step 4: Run rule engine
        rule_score, rule_results = self._run_rules(transaction, features)

        # Step 5: Combine scores (weighted average)
        final_score = self._combine_scores(ml_score, rule_score)

        # Step 6: Predict label based on final score
        predicted_label = self._score_to_label(final_score)

        # Step 7: Generate prediction record
        prediction = Prediction(
            transaction_id=transaction_id,
            model_version_id="v1.0.0",
            predicted_label=predicted_label,
            confidence_score=final_score,
            probability_score=ml_score,
            inference_time_ms=0,  # Track actual latency
            prediction_timestamp=datetime.now(timezone.utc),
        )

        # Step 8: Store rule results as explanations
        for rule_result in rule_results:
            if rule_result.triggered:
                explanation = PredictionExplanation(
                    prediction=prediction,
                    feature_name=rule_result.rule_name,
                    feature_value=rule_result.score,
                    contribution=rule_result.score,
                    display_order=len(prediction.explanations),
                )
                prediction.explanations.append(explanation)

        # Step 9: Save prediction
        self.db_session.add(prediction)
        await self.db_session.flush()

        # Step 10: Generate alert if needed
        if final_score > 0.7:
            await self._generate_fraud_alert(transaction, prediction, rule_results)

        # Step 11: Update transaction risk level
        await self._update_transaction_risk(transaction, final_score)

        return prediction

    def _run_ml_model(self, features: dict[str, Any]) -> float:
        """
        Run ML model inference.

        Args:
            features: Feature vector

        Returns:
            ML model probability score (0-1)
        """
        if self.ml_model is None:
            # No model loaded, return 0
            return 0.0

        try:
            # Convert features to array
            feature_names = self.feature_extractor.get_feature_names()
            feature_types = self.feature_extractor.get_feature_types()
            X = np.array([[features.get(f, 0.0) for f in feature_names]])


            proba = self.ml_model.predict_proba(X)
            return float(proba[0][1])  # Probability of fraud class
        except Exception as e:
            # Log error
            print(f"ML model inference error: {e}")
            return 0.0

    def _run_rules(
        self,
        transaction: Transaction,
        features: dict[str, Any],
    ) -> tuple[float, list[RuleResult]]:
        """
        Run rule engine.

        Args:
            transaction: Transaction object
            features: Feature vector

        Returns:
            Tuple of (composite_rule_score, rule_results)
        """
        transaction_data = {
            "amount": float(transaction.amount),
            "timestamp": transaction.transaction_timestamp.isoformat(),
            "channel": transaction.channel.value if transaction.channel else None,
        }

        return self.rule_engine.evaluate(transaction_data, features)

    def _combine_scores(self, ml_score: float, rule_score: float) -> float:
        """
        Combine ML and rule scores.

        Uses weighted average with rule score as floor.

        Args:
            ml_score: ML model probability
            rule_score: Rule engine composite score

        Returns:
            Combined risk score (0-1)
        """
        # Weighted combination
        ml_weight = 0.6
        rule_weight = 0.4

        combined = (ml_score * ml_weight) + (rule_score * rule_weight)

        # Rule score acts as floor
        combined = max(combined, rule_score)

        return min(1.0, max(0.0, combined))

    def _score_to_label(self, score: float) -> PredictionLabel:
        """
        Convert score to prediction label.

        Args:
            score: Risk score (0-1)

        Returns:
            PredictionLabel
        """
        if score >= 0.8:
            return PredictionLabel.FRAUD
        elif score >= 0.5:
            return PredictionLabel.SUSPICIOUS
        else:
            return PredictionLabel.LEGITIMATE

    async def _generate_fraud_alert(
        self,
        transaction: Transaction,
        prediction: Prediction,
        rule_results: list[RuleResult],
    ) -> FraudAlert:
        """
        Generate fraud alert for high-risk predictions.

        Args:
            transaction: Transaction object
            prediction: Prediction result
            rule_results: Rule evaluation results

        Returns:
            Created FraudAlert
        """
        triggered_rules = [r for r in rule_results if r.triggered]

        # Determine severity
        high_severity_rules = [r for r in triggered_rules if r.severity == RuleSeverity.CRITICAL]
        if high_severity_rules:
            severity = "critical"
        elif prediction.confidence_score and prediction.confidence_score > 0.9:
            severity = "high"
        else:
            severity = "medium"

        # Build alert
        alert = FraudAlert(
            transaction_id=transaction.id,
            prediction_id=prediction.id,
            alert_type="fraud_detection",
            severity=severity,
            title=f"Fraud detected: {prediction.predicted_label.value}",
            description=f"Transaction flagged with risk score {prediction.confidence_score:.2f}. "
                       f"{len(triggered_rules)} rules triggered.",
            risk_score=prediction.confidence_score,
            metadata={
                "triggered_rules": [r.rule_id for r in triggered_rules],
                "rule_explanations": [r.explanation for r in triggered_rules],
                "ml_score": prediction.probability_score,
            },
        )

        self.db_session.add(alert)
        await self.db_session.flush()

        return alert

    async def _update_transaction_risk(
        self,
        transaction: Transaction,
        risk_score: float,
    ) -> None:
        """
        Update transaction risk level.

        Args:
            transaction: Transaction object
            risk_score: Calculated risk score
        """
        # Map score to risk level
        if risk_score >= 0.8:
            risk_level_code = "HIGH"
        elif risk_score >= 0.5:
            risk_level_code = "MEDIUM"
        else:
            risk_level_code = "LOW"

        # Load risk level
        risk_level = await self.db_session.execute(
            select(RiskLevelCode).where(RiskLevelCode.code == risk_level_code)
        )
        risk_level = risk_level.scalar_one_or_none()

        if risk_level:
            transaction.risk_level_id = risk_level.id
            await self.db_session.flush()
