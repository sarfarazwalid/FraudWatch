"""
RolePermission junction table for many-to-many relationship between roles and permissions.

This is an association table that links roles to their permissions.
"""

from typing import Optional
from uuid import UUID as PyUUID

from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base
from app.models.mixins import (
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    VersionMixin,
)

if TYPE_CHECKING:
    from app.models.identity.role import Role
    from app.models.identity.permission import Permission


class RolePermission(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Junction table for Role-Permission many-to-many relationship.
    """
    __tablename__ = "role_permissions"

    role_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )

    permission_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # No relationships to avoid circular dependency
    # Use explicit queries to access related Role and Permission data if needed

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )
