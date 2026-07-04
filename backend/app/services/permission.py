"""
Permission service.

Handles permission management business logic.
"""

from typing import Optional

from app.models.identity.permission import Permission
from app.repositories.permission import PermissionRepository


class PermissionService:
    """
    Service for permission operations.
    
    Handles permission creation, updates, and queries.
    """
    
    def __init__(self, permission_repo: PermissionRepository):
        self.permission_repo = permission_repo
    
    async def get_permission(self, permission_id: str) -> Optional[Permission]:
        """Get permission by ID."""
        return await self.permission_repo.get(permission_id)
    
    async def get_permission_by_name(self, name: str) -> Optional[Permission]:
        """Get permission by name."""
        return await self.permission_repo.get_by_name(name)
    
    async def get_permission_by_resource_and_action(self, resource: str, action: str) -> Optional[Permission]:
        """Get permission by resource and action."""
        return await self.permission_repo.get_by_resource_and_action(resource, action)
    
    async def create_permission(self, name: str, description: str, resource: str, action: str) -> Permission:
        """
        Create a new permission.
        
        Args:
            name: Permission name
            description: Permission description
            resource: Resource name
            action: Action name
            
        Returns:
            Created permission
        """
        permission = Permission(
            name=name,
            description=description,
            resource=resource,
            action=action,
        )
        
        self.permission_repo.session.add(permission)
        await self.permission_repo.session.flush()
        await self.permission_repo.session.refresh(permission)
        
        return permission
    
    async def get_permissions_by_resource(self, resource: str) -> list[Permission]:
        """Get all permissions for a resource."""
        return await self.permission_repo.get_permissions_by_resource(resource)
    
    async def get_all_permissions(self, skip: int = 0, limit: int = 100) -> list[Permission]:
        """Get all permissions."""
        return await self.permission_repo.get_all(skip=skip, limit=limit)
    
    async def search_permissions(self, query: str, skip: int = 0, limit: int = 100) -> list[Permission]:
        """Search permissions by query."""
        return await self.permission_repo.search_permissions(query, skip=skip, limit=limit)