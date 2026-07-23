"""
Session Repository Implementation.

Data access layer for UserSession model with specific query methods.
"""

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any, List, Optional

from app.models.identity.user_session import UserSession
from app.models.enums import SessionStatus
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[UserSession, Any, Any]):
    """
    Repository for UserSession model.

    Provides session-specific query methods.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(UserSession, session)

    async def get_by_token_jti(self, token_jti: str) -> Optional[UserSession]:
        """Get session by token JTI."""
        return await self.get_by_field("token_jti", token_jti)

    async def get_active_sessions_for_user(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for a user."""
        return await self.get_all(
            filters={"user_id": user_id, "status": SessionStatus.ACTIVE}
        )

    async def get_expired_sessions(self) -> List[UserSession]:
        """Get all expired sessions."""
        result = await self.session.execute(
            select(UserSession).where(
                UserSession.expires_at < datetime.now(timezone.utc),
                UserSession.status == SessionStatus.ACTIVE
            )
        )
        return list(result.scalars().all())

    async def revoke_session(self, session_id: str) -> bool:
        """Revoke a session."""
        session = await self.get(session_id)
        if session:
            session.status = SessionStatus.REVOKED
            await self.session.flush()
            return True
        return False

    async def revoke_all_user_sessions(self, user_id: str, except_session_id: Optional[str] = None) -> None:
        """Revoke all sessions for a user, optionally keeping one active."""
        query = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.status == SessionStatus.ACTIVE
        )

        if except_session_id:
            query = query.where(UserSession.id != except_session_id)

        result = await self.session.execute(query)
        sessions = result.scalars().all()

        for s in sessions:
            s.status = SessionStatus.REVOKED

        await self.session.flush()

    async def cleanup_expired_sessions(self) -> int:
        """Delete expired sessions (maintenance task)."""
        result = await self.session.execute(
            select(UserSession).where(
                UserSession.expires_at < datetime.now(timezone.utc)
            )
        )
        sessions = result.scalars().all()
        for s in sessions:
            await self.session.delete(s)
        await self.session.flush()
        return len(sessions)
