"""
FeatureImportance model for ML model feature importance tracking.

Stores global feature importance scores for ML model versions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Numeric, Integer, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, AuditMixin

if TYPE_CHECKING:
    from app.models.ml.model_version import ModelVersion


class FeatureImportance(Base, UUIDMixin, TimestampMixin, AuditMixin):
    """
    ML model feature importance scores.
    
    Stores global feature importance for model interpretability and explainability.
    Feature importance is model-specific and versioned.
    
    Design Rationale:
    - Model-agnostic: Supports any ML model type
    - Global importance: Overall feature contribution across all predictions
    - Ranked: Features ordered by importance score
    - Immutable: Importance scores never change once recorded
    - Explainability: Critical for model transparency and compliance
    
    Attributes:
        model_version_id: Model version this importance is for
        feature_name: Name of the feature
        importance_score: Importance score (normalized 0-1)
        ranking: Feature rank by importance
    """
    __tablename__ = "feature_importance"
    
    # Foreign Keys
    model_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("model_versions.id", name="fk_feature_importance_model_version_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Model version this importance is for",
    )
    
    # Feature Identity
    feature_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Name of the feature",
    )
    
    # Importance Score
    importance_score: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 8),  # 0.00000000 to 1.00000000
        nullable=True,
        doc="Feature importance score (0-1 normalized)",
    )
    
    # Ranking
    ranking: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Feature rank by importance (1 = most important)",
    )
    
    # Additional Context
    importance_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Type of importance (gain, cover, frequency, shap, etc.)",
    )
    
    # Relationships
    model_version: Mapped["ModelVersion"] = relationship(
        "ModelVersion",
        back_populates="feature_importances",
        lazy="selectin",
    )
    
    # Constraints
    __table_args__ = (
        Index("ix_feature_importance_model_version", "model_version_id"),
        Index("ix_feature_importance_ranking", "model_version_id", "ranking"),
        # Ensure unique feature names per model version
        Index("uq_feature_importance_model_feature", "model_version_id", "feature_name", unique=True),
        # CHECK constraints
        CheckConstraint(
            "importance_score IS NULL OR (importance_score >= 0 AND importance_score <= 1)",
            name="ck_feature_importance_score_range",
        ),
        CheckConstraint(
            "ranking IS NULL OR ranking > 0",
            name="ck_feature_importance_ranking_positive",
        ),
    )
    
    def __repr__(self) -> str:
        return f"<FeatureImportance {self.feature_name} score={self.importance_score} rank={self.ranking}>"