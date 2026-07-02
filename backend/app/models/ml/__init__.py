"""
Machine Learning Domain Models.

This module contains all SQLAlchemy ORM models for the Machine Learning domain.
The ML domain provides MLOps capabilities for model versioning, training tracking,
and prediction history.

Models:
    - DatasetMetadata: Tracks datasets used for training
    - TrainingRun: Records training execution metadata
    - ModelVersion: Versioned ML model records
    - ModelMetrics: Model evaluation metrics
    - FeatureImportance: Feature importance scores
    - PredictionHistory: Immutable prediction records
    - ModelRegistry: Production model lifecycle management

All models inherit from:
    - Base: Declarative base with naming conventions
    - UUIDMixin: UUID primary keys
    - TimestampMixin: created_at, updated_at timestamps
    - AuditMixin: created_by, updated_by audit fields

Domain Enums:
    - TrainingStatus: Training execution statuses
    - ModelStatus: Model lifecycle statuses
    - DeploymentEnvironment: Deployment environment types
    - PredictionStatus: Prediction processing statuses
    - AlgorithmType: ML algorithm types
    - FrameworkType: ML framework types
    - DatasetSource: Dataset source types
"""

from app.models.ml.dataset_metadata import DatasetMetadata
from app.models.ml.training_run import TrainingRun
from app.models.ml.model_version import ModelVersion
from app.models.ml.model_metrics import ModelMetrics
from app.models.ml.feature_importance import FeatureImportance
from app.models.ml.prediction_history import PredictionHistory
from app.models.ml.model_registry import ModelRegistry

__all__ = [
    "DatasetMetadata",
    "TrainingRun",
    "ModelVersion",
    "ModelMetrics",
    "FeatureImportance",
    "PredictionHistory",
    "ModelRegistry",
]