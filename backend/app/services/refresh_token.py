"""
Refresh token service.

Handles refresh token creation, validation, and rotation.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from app.models.identity.refresh_token import RefreshToken
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.services.jwt import JWTService
import logging

logger = logging.getLogger(__name__)


class RefreshTokenService:
    """
    Service for refresh token operations.

    Handles token creation, validation, rotation, and revocation.
    """

    def __init__(self, refresh_token_repo: RefreshTokenRepository, user_repo: UserRepository):
        self.refresh_token_repo = refresh_token_repo
        self.user_repo = user_repo

    async def create_token(self, user_id: str, device_info: Optional[str] = None, ip_address: Optional[str] = None) -> tuple[str, RefreshToken]:
        """
        Create a new refresh token.

        Args:
            user_id: User ID
            device_info: Optional device information
            ip_address: Optional IP address

        Returns:
            Tuple of (token_string, token_model)
        """
        # Generate family ID for token rotation
        family_id = str(uuid.uuid4())

        # Create JWT refresh token
        token_string = JWTService.create_refresh_token(user_id, family_id)

        # Calculate expiration (7 days from now)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # Create token record
        token = RefreshToken(
            user_id=user_id,
            token_jti=token_string,
            family_id=family_id,
            expires_at=expires_at,
        )

        self.refresh_token_repo.session.add(token)
        await self.refresh_token_repo.session.flush()
        await self.refresh_token_repo.session.refresh(token)

        logger.info(f"Created refresh token for user {user_id}")
        return token_string, token

    async def validate_token(self, token_string: str) -> Optional[RefreshToken]:
        """
        Validate a refresh token.

        Args:
            token_string: Refresh token string

        Returns:
            RefreshToken if valid, None otherwise
        """
        # Decode JWT
        payload = JWTService.decode_token(token_string)

        if not payload or not JWTService.is_refresh_token(payload):
            logger.warning("Invalid or expired refresh token")
            return None

        user_id = JWTService.get_user_id(payload)
        if not user_id:
            return None

        # Check if token exists in database
        token = await self.refresh_token_repo.get_by_token_jti(token_string)
        if not token:
            logger.warning(f"Refresh token not found for user {user_id}")
            return None

        if token.is_revoked:
            logger.warning(f"Refresh token revoked for user {user_id}")
            return None

        # Check expiration
        if token.expires_at < datetime.now(timezone.utc):
            logger.warning(f"Refresh token expired for user {user_id}")
            # Clean up expired token
            await self.refresh_token_repo.session.delete(token)
            await self.refresh_token_repo.session.flush()
            return None

        return token

    async def rotate_token(self, old_token: RefreshToken) -> Optional[tuple[str, RefreshToken]]:
        """
        Rotate refresh token (create new one, revoke old one).

        Args:
            old_token: Old refresh token

        Returns:
            Tuple of (new_token_string, new_token_model) or None
        """
        # Revoke old token
        old_token.is_revoked = True
        await self.refresh_token_repo.session.flush()

        # Create new token with same family ID
        family_id = old_token.family_id

        # Create JWT refresh token
        token_string = JWTService.create_refresh_token(str(old_token.user_id), family_id)

        # Calculate expiration (7 days from now)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # Create new token record
        new_token = RefreshToken(
            user_id=old_token.user_id,
            token_jti=token_string,
            family_id=family_id,
            expires_at=expires_at,
        )

        self.refresh_token_repo.session.add(new_token)
        await self.refresh_token_repo.session.flush()
        await self.refresh_token_repo.session.refresh(new_token)

        logger.info(f"Rotated refresh token for user {old_token.user_id}")
        return token_string, new_token

    async def revoke_token(self, token_string: str) -> bool:
        """
        Revoke a refresh token.

        Args:
            token_string: Token to revoke

        Returns:
            True if revoked, False if not found
        """
        token = await self.refresh_token_repo.get_by_token_jti(token_string)
        if not token:
            return False

        token.is_revoked = True
        await self.refresh_token_repo.session.flush()
        return True

    async def revoke_all_user_tokens(self, user_id: str) -> None:
        """Revoke all refresh tokens for a user."""
        await self.refresh_token_repo.revoke_all_for_user(user_id)
        logger.info(f"Revoked all refresh tokens for user {user_id}")
