"""
Role Repository Implementation.

Data access layer for Role model with specific query methods.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Any, List, Optional

from app.models.identity.role import Role
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role, Any, Any]):
    """
    Repository for Role model.

    Provides role-specific query methods beyond generic CRUD.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Role, session)

    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        return await self.get_by_field("name", name)

    async def get_by_role_type(self, role_type: str) -> Optional[Role]:
        """Get role by type."""
        from app.models.enums import RoleType
        try:
            role_type_enum = RoleType(role_type)
        except ValueError:
            return None
        return await self.get_by_field("role_type", role_type_enum)

    async def get_system_roles(self) -> List[Role]:
        """Get all system roles."""
        return await self.get_all(filters={"is_system_role": True})

    async def get_roles_with_permissions(self) -> List[Role]:
        """Get all roles with their permissions loaded."""
        result = await self.session.execute(
            select(Role).options(selectinload(Role.permissions))
        )
        return list(result.scalars().unique().all())

    async def search_roles(self, query: str, skip: int = 0, limit: int = 100) -> List[Role]:
        """Search roles by name or description."""
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(Role).where(
                (Role.name.ilike(search_pattern)) |
                (Role.description.ilike(search_pattern))
            ).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
