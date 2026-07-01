"""
RolePermission junction table for many-to-many relationship between roles and permissions.

This is an association table that links roles to their permissions.
"""

from sqlalchemy import UUID, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin


class RolePermission(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Junction table for Role-Permission many-to-many relationship.
    """
    __tablename__ = "role_permissions"
    
    role_id: Mapped[UUID] = mapped_column(
        nullable=False,
    )
    
    permission_id: Mapped[UUID] = mapped_column(
        nullable=False,
    )
    
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )