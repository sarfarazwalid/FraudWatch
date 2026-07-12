"""
FraudWatch Machine Learning Layer

This package provides:
- Feature engineering and preprocessing
- ML model training, evaluation, and deployment
- Rule-based fraud detection
- Model registry and versioning
"""

__version__ = "1.0.0"

from ml.models.base_model import BaseMLModel
from ml.rules.base_rule import BaseRule, RuleResult

__all__ = [
    "BaseMLModel",
    "BaseRule",
    "RuleResult",
]
