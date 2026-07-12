"""
Permission Repository Implementation.

Data access layer for Permission model with specific query methods.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Any, List, Optional

from app.models.identity.permission import Permission
from app.repositories.base import BaseRepository


class PermissionRepository(BaseRepository[Permission, Any, Any]):
    """
    Repository for Permission model.

    Provides permission-specific query methods beyond generic CRUD.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Permission, session)

    async def get_by_name(self, name: str) -> Optional[Permission]:
        """Get permission by name."""
        return await self.get_by_field("name", name)

    async def get_by_resource_and_action(self, resource: str, action: str) -> Optional[Permission]:
        """Get permission by resource and action combination."""
        result = await self.session.execute(
            select(Permission).where(
                Permission.resource == resource,
                Permission.action == action
            )
        )
        return result.scalar_one_or_none()

    async def get_permissions_by_resource(self, resource: str) -> List[Permission]:
        """Get all permissions for a specific resource."""
        return await self.get_all(filters={"resource": resource})

    async def get_permissions_by_action(self, action: str) -> List[Permission]:
        """Get all permissions for a specific action."""
        return await self.get_all(filters={"action": action})

    async def search_permissions(self, query: str, skip: int = 0, limit: int = 100) -> List[Permission]:
        """Search permissions by name or description."""
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(Permission).where(
                (Permission.name.ilike(search_pattern)) |
                (Permission.description.ilike(search_pattern)) |
                (Permission.resource.ilike(search_pattern))
            ).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_with_roles(self) -> List[Permission]:
        """Get all permissions with their roles loaded."""
        # Note: roles relationship removed to break circular dependency
        # Roles can be queried separately via role_permissions table
        return await self.get_all()
