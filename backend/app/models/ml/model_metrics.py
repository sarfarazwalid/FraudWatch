"""
ModelMetrics model for ML model evaluation metrics tracking.

Stores evaluation metrics for ML model versions.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import func

from sqlalchemy import String, Numeric, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, AuditMixin

if TYPE_CHECKING:
    from app.models.ml.model_version import ModelVersion


class ModelMetrics(Base, UUIDMixin, TimestampMixin, AuditMixin):
    """
    ML model evaluation metrics.
    
    Stores performance metrics for a specific model version.
    Metrics are immutable once recorded to preserve evaluation integrity.
    
    Design Rationale:
    - Immutable: Metrics never change after evaluation
    - Normalized: Standard metric names and ranges (0-1)
    - Complete: All standard classification metrics included
    - Timestamped: Evaluation timestamp for time-series analysis
    - Versioned: Each model version has at most one metrics record
    
    Attributes:
        model_version_id: Model version being evaluated
        accuracy: Overall accuracy
        precision: Precision score
        recall: Recall score
        f1_score: F1 score
        roc_auc: ROC AUC score
        log_loss: Logarithmic loss
        false_positive_rate: False positive rate
        false_negative_rate: False negative rate
        evaluation_timestamp: When evaluation was performed
    """
    __tablename__ = "model_metrics"
    
    # Foreign Keys
    model_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("model_versions.id", name="fk_model_metrics_model_version_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One metrics record per model version
        index=True,
        doc="Model version being evaluated",
    )
    
    # Classification Metrics
    accuracy: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),  # 0.0000 to 1.0000
        nullable=True,
        doc="Overall accuracy (0-1)",
    )
    
    precision: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Precision score (0-1)",
    )
    
    recall: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Recall score (0-1)",
    )
    
    f1_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="F1 score (0-1)",
    )
    
    roc_auc: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="ROC AUC score (0-1)",
    )
    
    log_loss: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 6),  # Can be > 1
        nullable=True,
        doc="Logarithmic loss",
    )
    
    # Confusion Matrix Metrics
    false_positive_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="False positive rate (0-1)",
    )
    
    false_negative_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="False negative rate (0-1)",
    )
    
    # Additional Metrics
    mean_absolute_error: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 6),
        nullable=True,
        doc="Mean absolute error (for regression)",
    )
    
    mean_squared_error: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 6),
        nullable=True,
        doc="Mean squared error (for regression)",
    )
    
    r2_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="R² score (for regression)",
    )
    
    # Evaluation Context
    evaluation_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        doc="When evaluation was performed",
    )
    
    evaluation_dataset_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Hash of evaluation dataset for reproducibility",
    )
    
    # Relationships
    model_version: Mapped["ModelVersion"] = relationship(
        "ModelVersion",
        back_populates="metrics",
        lazy="selectin",
        uselist=False,
    )
    
    # Constraints
    __table_args__ = (
        Index("ix_model_metrics_version", "model_version_id"),
        Index("ix_model_metrics_timestamp", "evaluation_timestamp"),
        # CHECK constraints for metric ranges
        CheckConstraint(
            "accuracy IS NULL OR (accuracy >= 0 AND accuracy <= 1)",
            name="ck_model_metrics_accuracy_range",
        ),
        CheckConstraint(
            "precision IS NULL OR (precision >= 0 AND precision <= 1)",
            name="ck_model_metrics_precision_range",
        ),
        CheckConstraint(
            "recall IS NULL OR (recall >= 0 AND recall <= 1)",
            name="ck_model_metrics_recall_range",
        ),
        CheckConstraint(
            "f1_score IS NULL OR (f1_score >= 0 AND f1_score <= 1)",
            name="ck_model_metrics_f1_range",
        ),
        CheckConstraint(
            "roc_auc IS NULL OR (roc_auc >= 0 AND roc_auc <= 1)",
            name="ck_model_metrics_roc_auc_range",
        ),
        CheckConstraint(
            "false_positive_rate IS NULL OR (false_positive_rate >= 0 AND false_positive_rate <= 1)",
            name="ck_model_metrics_fpr_range",
        ),
        CheckConstraint(
            "false_negative_rate IS NULL OR (false_negative_rate >= 0 AND false_negative_rate <= 1)",
            name="ck_model_metrics_fnr_range",
        ),
    )
    
    def __repr__(self) -> str:
        return f"<ModelMetrics accuracy={self.accuracy} f1={self.f1_score}>"