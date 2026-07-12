"""
ModelVersion model for ML model lifecycle management.

Represents a versioned ML model with complete metadata for MLOps.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Integer, Enum, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, AuditMixin
from app.models.ml.enums import ModelStatus, AlgorithmType, FrameworkType

if TYPE_CHECKING:
    from app.models.ml.training_run import TrainingRun
    from app.models.ml.model_metrics import ModelMetrics
    from app.models.ml.feature_importance import FeatureImportance
    from app.models.ml.prediction_history import PredictionHistory


class ModelVersion(Base, UUIDMixin, TimestampMixin, AuditMixin):
    """
    Immutable ML model version record.

    Represents a specific version of an ML model with complete metadata.
    Model versions are immutable once created to preserve reproducibility.

    Design Rationale:
    - Immutable: Model versions never modified after creation
    - Versioned: Unique per model_name with incremental version numbers
    - Complete metadata: Algorithm, framework, artifact path, checksum
    - Lineage: Links to training run for full reproducibility
    - Lifecycle: Status and deployment tracking
    - Artifacts: Model file location and integrity verification

    Attributes:
        version: Model version number
        model_name: Model identifier
        algorithm: ML algorithm used
        framework: ML framework/library
        artifact_path: Path to serialized model
        checksum: SHA256 checksum of model artifact
        training_run_id: Associated training run
        status: Current model status
        deployed: Whether model is deployed
        deployment_date: When model was deployed
        created_at: When model version was created
    """
    __tablename__ = "model_versions"

    # Model Identity
    model_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Model identifier name",
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        doc="Model version number (incremental)",
    )

    # Model Configuration
    algorithm: Mapped[AlgorithmType] = mapped_column(
        Enum(AlgorithmType, name="algorithm_type", create_constraint=True),
        nullable=False,
        doc="ML algorithm used",
    )

    framework: Mapped[FrameworkType] = mapped_column(
        Enum(FrameworkType, name="framework_type", create_constraint=True),
        nullable=False,
        doc="ML framework/library",
    )

    # Model Artifact
    artifact_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        doc="Path to serialized model artifact",
    )

    checksum: Mapped[str] = mapped_column(
        String(64),  # SHA256 hex string
        nullable=False,
        doc="SHA256 checksum of model artifact for integrity verification",
    )

    # Training Lineage
    training_run_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("training_runs.id", name="fk_model_versions_training_run_id"),
        nullable=True,
        index=True,
        doc="Associated training run",
    )

    # Model Lifecycle
    status: Mapped[ModelStatus] = mapped_column(
        Enum(ModelStatus, name="model_status", create_constraint=True),
        nullable=False,
        server_default=ModelStatus.DRAFT.value,
        index=True,
        doc="Current model lifecycle status",
    )

    deployed: Mapped[bool] = mapped_column(
        nullable=False,
        server_default="false",
        doc="Whether model is currently deployed",
    )

    deployment_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When model was deployed (if deployed)",
    )

    # Additional Metadata
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Model description and purpose",
    )

    hyperparameters: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON string of hyperparameters used",
    )

    training_duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Training duration in seconds",
    )

    # Relationships
    training_run: Mapped[Optional["TrainingRun"]] = relationship(
        "TrainingRun",
        back_populates="model_versions",
        lazy="selectin",
    )

    metrics: Mapped[Optional["ModelMetrics"]] = relationship(
        "ModelMetrics",
        back_populates="model_version",
        lazy="selectin",
        uselist=False,
        cascade="all, delete-orphan",
    )

    feature_importances: Mapped[list["FeatureImportance"]] = relationship(
        "FeatureImportance",
        back_populates="model_version",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    predictions: Mapped[list["PredictionHistory"]] = relationship(
        "PredictionHistory",
        back_populates="model_version",
        lazy="selectin",
    )

    # Indexes
    __table_args__ = (
        Index("ix_model_versions_model_name", "model_name"),
        Index("ix_model_versions_version", "version"),
        Index("ix_model_versions_status", "status"),
        Index("ix_model_versions_training_run", "training_run_id"),
        Index("ix_model_versions_deployed", "deployed"),
        Index("ix_model_versions_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ModelVersion {self.model_name}:{self.version} status={self.status}>"
