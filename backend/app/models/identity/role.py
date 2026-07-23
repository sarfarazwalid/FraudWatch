"""
Role model for RBAC (Role-Based Access Control).

Represents a user role that can be assigned to users.
Roles contain permissions and define what actions users can perform.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import (
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    VersionMixin,
)
from app.models.enums import RoleType
from sqlalchemy import Enum as SAEnum

if TYPE_CHECKING:
    from app.models.identity.permission import Permission
    from app.models.identity.role_permission import RolePermission
    from app.models.identity.user import User


def _get_role_type_values(enum_class: type[RoleType]) -> list[str]:
    """Return list of enum values for SQLAlchemy Enum definition."""
    return [e.value for e in enum_class]


class Role(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Role model for access control.

    Roles define a set of permissions that can be assigned to users.
    System roles are pre-defined and cannot be modified.
    """
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    role_type: Mapped[RoleType] = mapped_column(
        SAEnum(RoleType, name='role_type', create_type=False, values_callable=_get_role_type_values),
    )

    is_system_role: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Relationships
    users: Mapped[list[User]] = relationship(
        "User",
        back_populates="role",
        lazy="selectin",
    )

    permissions: Mapped[list[Permission]] = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin",
        overlaps="role_permissions",
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
