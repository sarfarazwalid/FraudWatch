"""
TrainingRun model for ML training execution tracking.

Stores metadata about every training execution for reproducibility and audit.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Integer, Enum, DateTime, Text, ForeignKey, Index, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, AuditMixin
from app.models.ml.enums import TrainingStatus

if TYPE_CHECKING:
    from app.models.ml.dataset_metadata import DatasetMetadata
    from app.models.ml.model_version import ModelVersion


class TrainingRun(Base, UUIDMixin, TimestampMixin, AuditMixin):
    """
    ML training execution metadata.
    
    Records every training run with complete context for reproducibility,
    debugging, and model lineage tracking.
    
    Design Rationale:
    - Immutable: Training runs never modified after completion
    - Complete context: All parameters and conditions preserved
    - Lineage: Links datasets to model versions
    - Reproducibility: Git commit and random seed enable exact reproduction
    - Accountability: initiated_by tracks who started training
    
    Attributes:
        run_name: Human-readable training run identifier
        dataset_id: Dataset used for training
        started_at: Training start timestamp
        completed_at: Training completion timestamp
        duration_seconds: Training duration
        initiated_by: User who started training
        training_status: Current training status
        random_seed: Random seed for reproducibility
        git_commit_hash: Git commit for code versioning
        notes: Additional training context
    """
    __tablename__ = "training_runs"
    
    # Foreign Keys
    dataset_id: Mapped[UUID] = mapped_column(
        ForeignKey("dataset_metadata.id", name="fk_training_runs_dataset_id"),
        nullable=False,
        index=True,
        doc="Dataset used for training",
    )
    
    # Run Identity
    run_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Human-readable training run identifier",
    )
    
    # Training Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Training start timestamp",
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Training completion timestamp",
    )
    
    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Training duration in seconds",
    )
    
    # Training Context
    initiated_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", name="fk_training_runs_initiated_by"),
        nullable=True,
        doc="User who initiated training",
    )
    
    training_status: Mapped[TrainingStatus] = mapped_column(
        Enum(TrainingStatus, name="training_status", create_constraint=True),
        nullable=False,
        server_default=TrainingStatus.PENDING.value,
        index=True,
        doc="Current training execution status",
    )
    
    # Reproducibility
    random_seed: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Random seed for reproducibility",
    )
    
    git_commit_hash: Mapped[Optional[str]] = mapped_column(
        String(40),  # SHA-1
        nullable=True,
        doc="Git commit hash for code versioning",
    )
    
    # Additional Context
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Additional training context and notes",
    )
    
    hyperparameters: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON string of hyperparameters used",
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if training failed",
    )
    
    # Relationships
    dataset: Mapped["DatasetMetadata"] = relationship(
        "DatasetMetadata",
        back_populates="training_runs",
        lazy="selectin",
    )
    
    model_versions: Mapped[list["ModelVersion"]] = relationship(
        "ModelVersion",
        back_populates="training_run",
        lazy="selectin",
        doc="Model versions produced by this training run",
    )
    
    # Constraints
    __table_args__ = (
        Index("ix_training_runs_dataset_id", "dataset_id"),
        Index("ix_training_runs_status", "training_status"),
        Index("ix_training_runs_started_at", "started_at"),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="ck_training_runs_duration_positive",
        ),
    )
    
    def __repr__(self) -> str:
        return f"<TrainingRun {self.run_name} status={self.training_status}>"