"""
User service.

Handles user management business logic.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

from app.models.identity.user import User
from app.models.enums import UserStatus
from app.repositories.user import UserRepository
from app.repositories.role import RoleRepository
from app.services.password import PasswordService


class UserService:
    """
    Service for user operations.

    Handles user creation, updates, and profile management.
    """

    def __init__(self, user_repo: UserRepository, role_repo: RoleRepository):
        self.user_repo = user_repo
        self.role_repo = role_repo

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return await self.user_repo.get(user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await self.user_repo.get_by_email(email)

    async def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        username: Optional[str] = None,
        phone_number: Optional[str] = None,
        role_id: Optional[str] = None
    ) -> User:
        """
        Create a new user.

        Args:
            email: User email
            password: Plain text password
            first_name: User first name
            last_name: User last name
            username: Optional username
            phone_number: Optional phone number
            role_id: Optional role ID

        Returns:
            Created user
        """
        # Hash password
        password_hash = PasswordService.hash(password)


        if not role_id:
            role = await self.role_repo.get_by_role_type("viewer")
            if role:
                role_id = str(role.id)

        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            username=username,
            phone_number=phone_number,
            status=UserStatus.PENDING_VERIFICATION,
        )

        self.user_repo.session.add(user)
        await self.user_repo.session.flush()
        await self.user_repo.session.refresh(user)

        # Assign role if provided
        if role_id:
            from app.models.identity.role import Role
            role = await self.role_repo.get(role_id)
            if role:
                user.role = role

        return user

    async def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """
        Update user fields.

        Args:
            user_id: User ID
            **kwargs: Fields to update

        Returns:
            Updated user or None
        """
        user = await self.user_repo.get(user_id)
        if not user:
            return None

        # Update allowed fields
        allowed_fields = ["first_name", "last_name", "username", "phone_number", "timezone", "language", "profile_image_url"]
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(user, field, value)

        await self.user_repo.session.flush()
        await self.user_repo.session.refresh(user)
        return user

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            True if changed, False otherwise
        """
        user = await self.user_repo.get(user_id)
        if not user:
            return False

        # Verify current password
        if not PasswordService.verify(current_password, user.password_hash):
            return False

        # Hash and set new password
        user.password_hash = PasswordService.hash(new_password)
        await self.user_repo.session.flush()

        return True

    async def verify_email(self, user_id: str) -> bool:
        """Mark user email as verified."""
        user = await self.user_repo.get(user_id)
        if not user:
            return False

        user.is_verified = True
        user.status = UserStatus.ACTIVE
        await self.user_repo.session.flush()
        return True

    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account."""
        user = await self.user_repo.get(user_id)
        if not user:
            return False

        user.status = UserStatus.INACTIVE
        await self.user_repo.session.flush()
        return True

    async def get_user_with_role(self, user_id: str) -> Optional[User]:
        """Get user with role loaded."""
        user = await self.user_repo.get(user_id)
        if user:
            # Refresh to load relationships
            await self.user_repo.session.refresh(user, ["role"])
        return user

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[User], int]:
        """
        List users with pagination, search, and filters.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            search: Search term for email, username, first name, last name
            filters: Dictionary of field filters
            sort_by: Field to sort by
            sort_order: Sort direction ('asc' or 'desc')

        Returns:
            Tuple of (list of users, total count)
        """
        # Calculate offset
        skip = (page - 1) * page_size

        # Build filter dict for repository
        repo_filters = {}
        if filters:
            # Map API filters to repository filters
            if "status" in filters:
                status = filters["status"]
                repo_filters["status"] = status.value if hasattr(status, 'value') else status
            if "role_id" in filters:
                repo_filters["role_id"] = filters["role_id"]
            if "is_verified" in filters:
                repo_filters["is_verified"] = filters["is_verified"]
            if "email" in filters:
                repo_filters["email"] = filters["email"]

        # Use search if provided
        if search:
            users = await self.user_repo.search_users(
                query=search,
                skip=skip,
                limit=page_size,
            )

            total = len(users)  # This is approximate
        else:

            users = await self.user_repo.get_all(
                skip=skip,
                limit=page_size,
                filters=repo_filters if repo_filters else None,
                order_by=sort_by if sort_order == "asc" else f"-{sort_by}",
            )

            total = await self.user_repo.count(filters=repo_filters if repo_filters else None)
            total = await self.user_repo.count(filters=repo_filters if repo_filters else None)

        return users, total
