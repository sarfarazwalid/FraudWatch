"""
User Repository Implementation.

Data access layer for User model with specific query methods.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any, List, Optional
from datetime import datetime, timedelta, timezone

from app.models.identity.user import User
from app.models.enums import UserStatus
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, Any, Any]):
    """
    Repository for User model.

    Provides user-specific query methods beyond generic CRUD.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return await self.get_by_field("email", email)

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return await self.get_by_field("username", username)

    async def get_by_external_id(self, external_id: str) -> Optional[User]:
        """Get user by external ID (for SSO)."""
        return await self.get_by_field("external_id", external_id)

    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get all active users."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"status": "active", "deleted_at": None}
        )

    async def get_locked_users(self) -> List[User]:
        """Get all locked users."""
        result = await self.session.execute(
            select(User).where(
                User.status == "locked",
                User.locked_until > datetime.now(timezone.utc)
            )
        )
        return list(result.scalars().all())

    async def get_users_with_expired_sessions(self) -> List[User]:
        """Get users with expired sessions."""
        result = await self.session.execute(
            select(User).join(
                User.sessions
            ).where(
                User.sessions.property.mapper.class_.expires_at < datetime.now(timezone.utc),
                User.sessions.property.mapper.class_.status == "active"
            )
        )
        return list(result.scalars().all())

    async def increment_failed_login(self, user_id: str) -> None:
        """Increment failed login attempts."""
        user = await self.get(user_id)
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.status = UserStatus.LOCKED
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)

            await self.session.flush()

    async def reset_failed_login(self, user_id: str) -> None:
        """Reset failed login attempts after successful login."""
        user = await self.get(user_id)
        if user:
            user.failed_login_attempts = 0
            user.locked_until = None
            if user.status == UserStatus.LOCKED:
                user.status = UserStatus.ACTIVE
            await self.session.flush()

    async def update_last_login(self, user_id: str) -> None:
        """Update last login timestamp."""
        user = await self.get(user_id)
        if user:
            user.last_login = datetime.now(timezone.utc)
            await self.session.flush()

    async def search_users(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Search users by email, username, first name, or last name."""
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(User).where(
                (User.email.ilike(search_pattern)) |
                (User.username.ilike(search_pattern)) |
                (User.first_name.ilike(search_pattern)) |
                (User.last_name.ilike(search_pattern))
            ).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(self, status: str) -> int:
        """Count users by status."""
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.status == status)
        )
        return result.scalar_one()
