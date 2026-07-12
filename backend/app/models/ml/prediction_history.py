"""
PredictionHistory model for ML prediction tracking.

Stores immutable prediction history for model monitoring and audit.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Integer, Enum, DateTime, ForeignKey, Index, Numeric, Text, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, AuditMixin
from app.models.ml.enums import PredictionStatus

if TYPE_CHECKING:
    from app.models.transaction.transaction import Transaction
    from app.models.ml.model_version import ModelVersion
    from app.models.fraud.prediction import Prediction


class PredictionHistory(Base, UUIDMixin, TimestampMixin, AuditMixin):
    """
    Immutable ML prediction history record.

    Stores every ML prediction made by model versions for audit,
    compliance, and model monitoring purposes.

    Design Rationale:
    - Immutable: Predictions never modified or deleted
    - Complete: Full context preserved (transaction, model, latency)
    - Model-agnostic: Links to model versions
    - Time-series: Partition-ready on prediction_timestamp
    - Audit: Permanent record for compliance

    Attributes:
        prediction_id: Unique prediction identifier
        transaction_id: Transaction being predicted
        model_version_id: Model version making prediction
        prediction_timestamp: When prediction was made
        latency_ms: Inference latency in milliseconds
        status: Prediction processing status
    """
    __tablename__ = "prediction_history"

    # Prediction Identity
    prediction_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="Unique prediction identifier",
    )

    # Foreign Keys
    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("transactions.id", name="fk_prediction_history_transaction_id"),
        nullable=False,
        index=True,
        doc="Transaction being predicted",
    )

    model_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("model_versions.id", name="fk_prediction_history_model_version_id"),
        nullable=False,
        index=True,
        doc="Model version that made the prediction",
    )

    # Prediction Context
    prediction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        doc="When prediction was generated",
    )

    latency_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Inference latency in milliseconds",
    )

    status: Mapped[PredictionStatus] = mapped_column(
        Enum(PredictionStatus, name="prediction_status", create_constraint=True),
        nullable=False,
        server_default=PredictionStatus.COMPLETED.value,
        doc="Prediction processing status",
    )

    # Additional Context
    input_features_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Hash of input features for reproducibility",
    )

    prediction_result: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Prediction result (fraud/legitimate/suspicious)",
    )

    confidence_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Model confidence score (0-1)",
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if prediction failed",
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        lazy="selectin",
        foreign_keys=[transaction_id],
    )

    model_version: Mapped["ModelVersion"] = relationship(
        "ModelVersion",
        back_populates="predictions",
        lazy="selectin",
    )

    # Link to Prediction in fraud domain (if exists)
    # Note: This is a simplified link - actual join requires proper FK
    # Disabled to avoid mapper configuration issues
    # fraud_prediction: Mapped[Optional["Prediction"]] = relationship(
    #     "Prediction",
    #     lazy="selectin",
    #     foreign_keys=[model_version_id],  # Simplified link
    #     viewonly=True,
    # )

    # Constraints
    __table_args__ = (
        Index("ix_prediction_history_transaction", "transaction_id"),
        Index("ix_prediction_history_model", "model_version_id"),
        Index("ix_prediction_history_timestamp", "prediction_timestamp"),
        Index("ix_prediction_history_status", "status"),
        # CHECK constraints
        CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0",
            name="ck_prediction_history_latency_positive",
        ),
    )

    def __repr__(self) -> str:
        return f"<PredictionHistory {self.prediction_id} model={self.model_version_id}>"
