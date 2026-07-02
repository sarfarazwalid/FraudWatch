"""
ModelRegistry model for ML production model lifecycle management.

Tracks production model deployments and enables rollback capabilities.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Integer, Enum, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, AuditMixin
from app.models.ml.enums import DeploymentEnvironment

if TYPE_CHECKING:
    from app.models.ml.model_version import ModelVersion


class ModelRegistry(Base, UUIDMixin, TimestampMixin, AuditMixin):
    """
    Production model registry entry.
    
    Tracks the current and previous production model versions for each model.
    Enables rollback and deployment management.
    
    Design Rationale:
    - Single source of truth: One registry entry per model name
    - Deployment tracking: Current version and deployment environment
    - Rollback support: Previous version preserved for quick rollback
    - Environment-aware: Supports multiple deployment environments
    - Active flag: Quick lookup of active production models
    
    Attributes:
        model_name: Model identifier
        current_version: Current production version
        previous_version: Previous production version (for rollback)
        deployment_environment: Deployment environment
        rollback_version: Version to rollback to
        active: Whether this registry entry is active
    """
    __tablename__ = "model_registry"
    
    # Model Identity
    model_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="Model identifier name",
    )
    
    # Version Tracking
    current_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Current production version number",
    )
    
    previous_version: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Previous production version number",
    )
    
    rollback_version: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Version to rollback to (if different from previous)",
    )
    
    # Deployment Context
    deployment_environment: Mapped[DeploymentEnvironment] = mapped_column(
        Enum(DeploymentEnvironment, name="deployment_environment", create_constraint=True),
        nullable=False,
        server_default=DeploymentEnvironment.PRODUCTION.value,
        index=True,
        doc="Current deployment environment",
    )
    
    deployed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When current version was deployed",
    )
    
    deployed_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", name="fk_model_registry_deployed_by"),
        nullable=True,
        doc="User who deployed current version",
    )
    
    # Registry State
    active: Mapped[bool] = mapped_column(
        nullable=False,
        server_default="true",
        index=True,
        doc="Whether this registry entry is active",
    )
    
    # Additional Context
    deployment_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Deployment notes and context",
    )
    
    # Relationships
    current_model_version: Mapped["ModelVersion"] = relationship(
        "ModelVersion",
        primaryjoin="and_(ModelRegistry.model_name == ModelVersion.model_name, ModelRegistry.current_version == ModelVersion.version)",
        foreign_keys=[model_name, current_version],
        lazy="selectin",
        viewonly=True,
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_model_registry_name", "model_name"),
        Index("ix_model_registry_environment", "deployment_environment"),
        Index("ix_model_registry_active", "active"),
    )
    
    def __repr__(self) -> str:
        return f"<ModelRegistry {self.model_name}:{self.current_version} env={self.deployment_environment}>"