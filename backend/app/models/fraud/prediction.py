"""
Prediction model for ML inference storage.

Stores immutable ML prediction records for audit and compliance.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Numeric, DateTime, ForeignKey, Integer, Text, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin
from app.models.fraud.enums import PredictionLabel

if TYPE_CHECKING:
    from app.models.transaction.transaction import Transaction
    from app.models.fraud.prediction_explanation import PredictionExplanation


class Prediction(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Immutable ML prediction record.
    
    Stores every ML prediction permanently for audit, compliance, and model monitoring.
    Predictions are never overwritten - each inference creates a new record.
    
    Design Rationale:
    - Immutable: Never updated, only inserted
    - Complete: Full inference context preserved
    - Model-agnostic: Supports multiple model versions
    - Time-series: Partition-ready on prediction_timestamp
    
    Attributes:
        transaction_id: FK to transaction being predicted
        model_version_id: ML model version identifier
        predicted_label: ML model prediction (fraud/legitimate/suspicious)
        confidence_score: Model confidence (0-1)
        probability_score: Raw probability score (0-1)
        inference_time_ms: Inference latency in milliseconds
        prediction_timestamp: When prediction was made
    """
    __tablename__ = "predictions"
    
    # Foreign Keys
    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("transactions.id", name="fk_predictions_transaction_id"),
        nullable=False,
        index=True,
        doc="Transaction being predicted",
    )
    
    # ML Model Context
    model_version_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="ML model version identifier",
    )
    
    # Prediction Results
    predicted_label: Mapped[PredictionLabel] = mapped_column(
        nullable=False,
        index=True,
        doc="ML model prediction label",
    )
    
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Model confidence score (0-1)",
    )
    
    probability_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Raw probability score (0-1)",
    )
    
    inference_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Inference latency in milliseconds",
    )
    
    prediction_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="When prediction was generated",
    )
    
    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        lazy="selectin",
        foreign_keys=[transaction_id],
    )
    
    explanations: Mapped[list["PredictionExplanation"]] = relationship(
        "PredictionExplanation",
        back_populates="prediction",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="PredictionExplanation.display_order.asc()",
    )
    
    # Constraints
    __table_args__ = (
        Index("ix_predictions_transaction_timestamp", "transaction_id", "prediction_timestamp"),
        Index("ix_predictions_model_timestamp", "model_version_id", "prediction_timestamp"),
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
            name="ck_predictions_confidence_score_range",
        ),
        CheckConstraint(
            "probability_score IS NULL OR (probability_score >= 0 AND probability_score <= 1)",
            name="ck_predictions_probability_score_range",
        ),
        CheckConstraint(
            "inference_time_ms IS NULL OR inference_time_ms >= 0",
            name="ck_predictions_inference_time_positive",
        ),
    )
    
    def __repr__(self) -> str:
        return f"<Prediction {self.id} label={self.predicted_label}>"