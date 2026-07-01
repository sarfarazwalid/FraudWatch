"""
Role model for RBAC (Role-Based Access Control).

Represents a user role that can be assigned to users.
Roles contain permissions and define what actions users can perform.
"""

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin
from app.models.enums import RoleType
from app.models.identity.permission import Permission
from app.models.identity.role_permission import RolePermission
from app.models.identity.user import User


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
    
    role_type: Mapped[RoleType] = mapped_column()
    
    is_system: Mapped[bool] = mapped_column(
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
    permissions: Mapped[list[Permission]] = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin",
    )
    
    users: Mapped[list[User]] = relationship(
        "User",
        back_populates="role",
        lazy="selectin",
    )
    
    role_permissions: Mapped[list[RolePermission]] = relationship(
        "RolePermission",
        back_populates="role",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Role {self.name}>"