"""
Refresh Token Repository Implementation.

Data access layer for RefreshToken model with specific query methods.
"""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any, List, Optional

from app.models.identity.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken, Any, Any]):
    """
    Repository for RefreshToken model.
    
    Provides refresh token-specific query methods.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(RefreshToken, session)
    
    async def get_by_token_jti(self, token_jti: str) -> Optional[RefreshToken]:
        """Get refresh token by JTI."""
        return await self.get_by_field("token_jti", token_jti)
    
    async def get_by_family_id(self, family_id: str) -> List[RefreshToken]:
        """Get all tokens in a family (for rotation detection)."""
        return await self.get_many_by_field("family_id", family_id)
    
    async def get_valid_tokens_for_user(self, user_id: str) -> List[RefreshToken]:
        """Get all valid (non-expired, non-revoked) refresh tokens for a user."""
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,  # noqa: E712
                RefreshToken.expires_at > datetime.utcnow()
            )
        )
        return list(result.scalars().all())
    
    async def revoke_token(self, token_jti: str) -> bool:
        """Revoke a refresh token."""
        token = await self.get_by_token_jti(token_jti)
        if token:
            token.revoked = True
            await self.session.flush()
            return True
        return False
    
    async def revoke_all_for_user(self, user_id: str) -> None:
        """Revoke all refresh tokens for a user."""
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False  # noqa: E712
            )
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.revoked = True
        await self.session.flush()
    
    async def cleanup_expired_tokens(self) -> int:
        """Delete expired tokens (maintenance task)."""
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.expires_at < datetime.utcnow()
            )
        )
        tokens = result.scalars().all()
        for token in tokens:
            await self.session.delete(token)
        await self.session.flush()
        return len(tokens)