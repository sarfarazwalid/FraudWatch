"""
Permission model for RBAC.

Represents a granular permission that can be assigned to roles.
Permissions define what actions can be performed on resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import PermissionAction
from app.models.mixins import (
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    VersionMixin,
)

if TYPE_CHECKING:
    from app.models.identity.role_permission import RolePermission
    from app.models.identity.role import Role


class Permission(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Permission model for fine-grained access control.

    Permissions represent the ability to perform an action on a resource.
    They are assigned to roles, not directly to users.
    """
    __tablename__ = "permissions"

    resource: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    action: Mapped[PermissionAction] = mapped_column(
        # values_callable makes SQLAlchemy use the enum *values* (lowercase)
        # instead of the enum *names* (uppercase), matching the PostgreSQL
        # permission_action enum labels (create, read, update, delete, execute).
        Enum(PermissionAction, name="permission_action", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Relationships
    # Note: No back_populates to avoid circular dependency with RolePermission
    role_permissions: Mapped[list[RolePermission]] = relationship(
        "RolePermission",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    roles: Mapped[list[Role]] = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
        lazy="selectin",
        overlaps="role_permissions",
    )

    def __repr__(self) -> str:
        return f"<Permission {self.resource}:{self.action}>"
