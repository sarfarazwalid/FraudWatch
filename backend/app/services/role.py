"""
Role service.

Handles role management business logic.
"""

from typing import Optional

from app.models.identity.role import Role
from app.models.enums import RoleType
from app.repositories.role import RoleRepository
from app.repositories.permission import PermissionRepository


class RoleService:
    """
    Service for role operations.

    Handles role creation, updates, and permission management.
    """

    def __init__(self, role_repo: RoleRepository, permission_repo: PermissionRepository):
        self.role_repo = role_repo
        self.permission_repo = permission_repo

    async def get_role(self, role_id: str) -> Optional[Role]:
        """Get role by ID."""
        return await self.role_repo.get(role_id)

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        return await self.role_repo.get_by_name(name)

    async def create_role(self, name: str, description: str, role_type: RoleType, permission_ids: Optional[list[str]] = None) -> Role:
        """
        Create a new role.

        Args:
            name: Role name
            description: Role description
            role_type: Role type
            permission_ids: List of permission IDs to assign

        Returns:
            Created role
        """
        role = Role(
            name=name,
            description=description,
            role_type=role_type,
        )

        self.role_repo.session.add(role)
        await self.role_repo.session.flush()
        await self.role_repo.session.refresh(role)

        # Assign permissions if provided
        if permission_ids:
            from app.models.identity.permission import Permission
            from app.models.identity.role_permission import RolePermission

            for perm_id in permission_ids:
                permission = await self.permission_repo.get(perm_id)
                if permission:
                    role_permission = RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                    )
                    self.role_repo.session.add(role_permission)

            await self.role_repo.session.flush()

        return role

    async def update_role(self, role_id: str, name: Optional[str] = None, description: Optional[str] = None, role_type: Optional[RoleType] = None) -> Optional[Role]:
        """
        Update role details.

        Args:
            role_id: Role ID
            name: New name (optional)
            description: New description (optional)
            role_type: New role type (optional)

        Returns:
            Updated role or None
        """
        role = await self.role_repo.get(role_id)
        if not role:
            return None

        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        if role_type is not None:
            role.role_type = role_type  # type: ignore

        await self.role_repo.session.flush()
        await self.role_repo.session.refresh(role)
        return role

    async def assign_permissions(self, role_id: str, permission_ids: list[str]) -> bool:
        """
        Assign permissions to a role.

        Args:
            role_id: Role ID
            permission_ids: List of permission IDs

        Returns:
            True if successful
        """
        from app.models.identity.role_permission import RolePermission

        role = await self.role_repo.get(role_id)
        if not role:
            return False

        # Clear existing permissions
        for rp in role.role_permissions:
            await self.role_repo.session.delete(rp)

        # Add new permissions
        for perm_id in permission_ids:
            permission = await self.permission_repo.get(perm_id)
            if permission:
                role_permission = RolePermission(
                    role_id=role.id,
                    permission_id=permission.id,
                )
                self.role_repo.session.add(role_permission)

        await self.role_repo.session.flush()
        return True

    async def check_permission(self, role_id: str, permission_name: str) -> bool:
        """
        Check if role has a specific permission.

        Args:
            role_id: Role ID
            permission_name: Permission name to check

        Returns:
            True if role has permission
        """
        role = await self.role_repo.get(role_id)
        if not role:
            return False

        # Check through role_permissions relationship
        from app.models.identity.role_permission import RolePermission
        return any(
            rp.permission.name == permission_name  # type: ignore
            for rp in role.role_permissions
            if rp.permission is not None
        )

    async def get_all_roles(self, skip: int = 0, limit: int = 100) -> list[Role]:
        """Get all roles."""
        return await self.role_repo.get_all(skip=skip, limit=limit)

    async def get_system_roles(self) -> list[Role]:
        """Get all system roles."""
        return await self.role_repo.get_system_roles()

    async def list_roles(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[dict] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> tuple[list[Role], int]:
        """List roles with pagination."""
        skip = (page - 1) * page_size
        repo_filters = {}
        if filters:
            if "is_active" in filters and filters["is_active"] is not None:
                repo_filters["is_active"] = filters["is_active"]
            if "role_type" in filters and filters["role_type"] is not None:
                repo_filters["role_type"] = filters["role_type"]

        if search:
            roles = await self.role_repo.search_roles(search, skip=skip, limit=page_size)
            total = len(roles)
        else:
            roles = await self.role_repo.get_all(
                skip=skip, limit=page_size,
                filters=repo_filters if repo_filters else None,
                order_by=sort_by if sort_order == "asc" else f"-{sort_by}",
            )
            total = await self.role_repo.count(filters=repo_filters if repo_filters else None)
        return roles, total

    async def get_role_with_permissions(self, role_id: str) -> Optional[Role]:
        """Get role with permissions loaded."""
        role = await self.role_repo.get(role_id)
        if role:
            await self.role_repo.session.refresh(role, ["permissions"])
        return role

    async def deactivate_role(self, role_id: str) -> bool:
        """Deactivate a role."""
        role = await self.role_repo.get(role_id)
        if not role:
            return False
        role.is_active = False
        await self.role_repo.session.flush()
        return True
