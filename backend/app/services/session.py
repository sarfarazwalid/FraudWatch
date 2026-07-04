"""
Session service.

Handles user session management and validation.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from app.models.identity.user_session import UserSession
from app.models.enums import SessionStatus
from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository
import logging

logger = logging.getLogger(__name__)


class SessionService:
    """
    Service for user session operations.
    
    Handles session creation, validation, and revocation.
    """
    
    def __init__(self, session_repo: SessionRepository, user_repo: UserRepository):
        self.session_repo = session_repo
        self.user_repo = user_repo
    
    async def create_session(
        self,
        user_id: str,
        session_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_in: Optional[timedelta] = None
    ) -> UserSession:
        """
        Create a new user session.
        
        Args:
            user_id: User ID
            session_token: Session token string
            ip_address: Optional IP address
            user_agent: Optional user agent
            expires_in: Optional expiration time
            
        Returns:
            Created session
        """
        if expires_in is None:
            expires_in = timedelta(hours=24)
        
        expires_at = datetime.utcnow() + expires_in
        
        session = UserSession(
            user_id=UUID(user_id),
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        
        self.session_repo.session.add(session)
        await self.session_repo.session.flush()
        await self.session_repo.session.refresh(session)
        
        return session
    
    async def get_session(self, session_token: str) -> Optional[UserSession]:
        """Get session by token."""
        return await self.session_repo.get_by_token_jti(session_token)
    
    async def validate_session(self, session_token: str) -> Optional[UserSession]:
        """
        Validate a session.
        
        Args:
            session_token: Session token
            
        Returns:
            Session if valid, None otherwise
        """
        session = await self.session_repo.get_by_token_jti(session_token)
        
        if not session:
            return None
        
        # Check if expired
        if session.expires_at < datetime.utcnow():
            session.status = SessionStatus.EXPIRED
            await self.session_repo.session.flush()
            return None
        
        # Check if revoked
        if session.status == SessionStatus.REVOKED:
            return None
        
        return session
    
    async def update_session_activity(self, session_token: str) -> Optional[UserSession]:
        """
        Update session last activity timestamp.
        
        Args:
            session_token: Session token
            
        Returns:
            Updated session or None
        """
        logger.info(f"Session activity update requested for token {session_token[:8]}...")
        # Note: UserSession model doesn't have last_activity field in current schema
        # This is a placeholder for future implementation
        session = await self.session_repo.get_by_token_jti(session_token)
        return session
    
    async def revoke_session(self, session_token: str) -> bool:
        """
        Revoke a session.
        
        Args:
            session_token: Session token
            
        Returns:
            True if revoked, False if not found
        """
        session = await self.session_repo.get_by_token_jti(session_token)
        if not session:
            return False
        
        session.status = SessionStatus.REVOKED
        session.revoked_at = datetime.utcnow()
        await self.session_repo.session.flush()
        return True
    
    async def revoke_all_user_sessions(self, user_id: str, except_session_token: Optional[str] = None) -> None:
        """
        Revoke all sessions for a user.
        
        Args:
            user_id: User ID
            except_session_token: Optional session token to keep active
        """
        await self.session_repo.revoke_all_user_sessions(user_id, except_session_id=except_session_token)
    
    async def get_user_sessions(self, user_id: str) -> list[UserSession]:
        """Get all active sessions for a user."""
        return await self.session_repo.get_active_sessions_for_user(user_id)
