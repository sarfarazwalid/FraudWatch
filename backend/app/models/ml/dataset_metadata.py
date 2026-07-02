"""
DatasetMetadata model for ML training data tracking.

Tracks datasets used for model training with lineage and quality metadata.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Integer, Enum, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, AuditMixin
from app.models.ml.enums import DatasetSource

if TYPE_CHECKING:
    from app.models.ml.training_run import TrainingRun


class DatasetMetadata(Base, UUIDMixin, TimestampMixin, AuditMixin):
    """
    Dataset metadata for ML training and evaluation.
    
    Tracks datasets used for model training with complete lineage information.
    Datasets are immutable once recorded to preserve training reproducibility.
    
    Design Rationale:
    - Lineage: Complete dataset provenance for audit and compliance
    - Immutable: Dataset records never change after creation
    - Reproducibility: Hash and storage path enable exact reproduction
    - Quality: Record count and feature count enable data quality monitoring
    
    Attributes:
        dataset_name: Human-readable dataset identifier
        source: Origin of the dataset
        record_count: Number of records in dataset
        feature_count: Number of features
        target_column: Name of target variable
        hash: SHA256 hash of dataset for integrity verification
        storage_path: Location where dataset is stored
        created_at: When dataset was registered
    """
    __tablename__ = "dataset_metadata"
    
    # Dataset Identity
    dataset_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="Human-readable dataset identifier",
    )
    
    source: Mapped[DatasetSource] = mapped_column(
        Enum(DatasetSource, name="dataset_source", create_constraint=True),
        nullable=False,
        index=True,
        doc="Origin/source of the dataset",
    )
    
    # Dataset Characteristics
    record_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Number of records in dataset",
    )
    
    feature_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Number of features in dataset",
    )
    
    target_column: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Name of target/label column",
    )
    
    # Dataset Integrity
    hash: Mapped[str] = mapped_column(
        String(64),  # SHA256 hex string
        nullable=False,
        unique=True,
        doc="SHA256 hash of dataset for integrity verification",
    )
    
    storage_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        doc="Storage location path (S3, GCS, filesystem, etc.)",
    )
    
    # Additional Metadata
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Dataset description and purpose",
    )
    
    schema_definition: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON schema or column definitions",
    )
    
    # Relationships
    training_runs: Mapped[list["TrainingRun"]] = relationship(
        "TrainingRun",
        back_populates="dataset",
        lazy="selectin",
        doc="Training runs using this dataset",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_dataset_metadata_name", "dataset_name"),
        Index("ix_dataset_metadata_source", "source"),
        Index("ix_dataset_metadata_hash", "hash", unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<DatasetMetadata {self.dataset_name} records={self.record_count} features={self.feature_count}>"