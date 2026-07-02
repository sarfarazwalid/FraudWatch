"""
Fraud Domain Models.

Contains all models related to fraud detection, investigation, and risk assessment:
- FraudAlert
- FraudCase
- FraudRule
- Prediction
- PredictionExplanation
- RiskAssessment
- InvestigationTimeline
- FraudComment
- FraudAttachment
"""

from app.models.fraud.fraud_alert import FraudAlert
from app.models.fraud.fraud_case import FraudCase
from app.models.fraud.fraud_rule import FraudRule
from app.models.fraud.prediction import Prediction
from app.models.fraud.prediction_explanation import PredictionExplanation
from app.models.fraud.risk_assessment import RiskAssessment
from app.models.fraud.investigation_timeline import InvestigationTimeline
from app.models.fraud.fraud_comment import FraudComment
from app.models.fraud.fraud_attachment import FraudAttachment

__all__ = [
    "FraudAlert",
    "FraudCase",
    "FraudRule",
    "Prediction",
    "PredictionExplanation",
    "RiskAssessment",
    "InvestigationTimeline",
    "FraudComment",
    "FraudAttachment",
]