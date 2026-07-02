"""
PredictionExplanation model for model-agnostic explanations.

Stores feature-level explanations for ML predictions using various XAI techniques.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Numeric, ForeignKey, Integer, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin
from app.models.fraud.enums import ExplanationMethod

if TYPE_CHECKING:
    from app.models.fraud.prediction import Prediction


class PredictionExplanation(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Model-agnostic prediction explanation.
    
    Stores feature-level explanations for individual predictions using various
    Explainable AI (XAI) techniques. Designed to support multiple explanation
    methods without model-specific dependencies.
    
    Design Rationale:
    - Model-agnostic: No SHAP/LIME-specific fields
    - Flexible: Supports various XAI techniques
    - Ordered: display_order for UI rendering
    - Complete: Stores feature names, values, and contributions
    
    Attributes:
        prediction_id: FK to prediction being explained
        explanation_method: XAI technique used
        feature_name: Name of the explained feature
        feature_value: Value of the feature for this prediction
        importance_score: Absolute importance magnitude
        contribution_direction: Positive/negative contribution to prediction
        display_order: Order for displaying in UI
    """
    __tablename__ = "prediction_explanations"
    
    # Foreign Keys
    prediction_id: Mapped[UUID] = mapped_column(
        ForeignKey("predictions.id", name="fk_prediction_explanations_prediction_id"),
        nullable=False,
        index=True,
        doc="Prediction being explained",
    )
    
    # Explanation Details
    explanation_method: Mapped[ExplanationMethod] = mapped_column(
        nullable=False,
        index=True,
        doc="XAI technique used (shap, lime, feature_importance, etc.)",
    )
    
    feature_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Name of the explained feature",
    )
    
    feature_value: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Value of the feature for this prediction",
    )
    
    importance_score: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 6),
        nullable=True,
        doc="Absolute importance magnitude",
    )
    
    contribution_direction: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Contribution direction (positive/negative)",
    )
    
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Display order in UI",
    )
    
    # Relationships
    prediction: Mapped["Prediction"] = relationship(
        "Prediction",
        back_populates="explanations",
        lazy="selectin",
    )
    
    # Constraints
    __table_args__ = (
        Index(
            "ix_prediction_explanations_prediction_order",
            "prediction_id",
            "display_order",
        ),
        Index(
            "ix_prediction_explanations_method_feature",
            "explanation_method",
            "feature_name",
        ),
        CheckConstraint(
            "importance_score IS NULL OR importance_score >= 0",
            name="ck_prediction_explanations_importance_positive",
        ),
    )
    
    def __repr__(self) -> str:
        return f"<PredictionExplanation {self.explanation_method}:{self.feature_name}>"