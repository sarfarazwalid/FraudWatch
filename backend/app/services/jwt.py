"""
JWT token service.

Handles JWT token creation, validation, and decoding.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4
from jose import JWTError, jwt
import logging
from app.config.settings import settings
from app.models.enums import TokenType

logger = logging.getLogger(__name__)


class JWTService:
    """
    Service for JWT token operations.

    Handles access token and refresh token creation/validation.
    """

    @staticmethod
    def create_access_token(
        user_id: str,
        role: str,
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[dict] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: User ID
            role: User role
            expires_delta: Optional custom expiration time
            additional_claims: Optional additional claims to include

        Returns:
            JWT access token string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)

        expire = datetime.now(timezone.utc) + expires_delta

        to_encode = {
            "sub": user_id,
            "role": role,
            "type": TokenType.ACCESS.value,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }

        if additional_claims:
            to_encode.update(additional_claims)

        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        user_id: str,
        family_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token.

        Args:
            user_id: User ID
            family_id: Token family ID for rotation tracking
            expires_delta: Optional custom expiration time

        Returns:
            JWT refresh token string
        """
        if expires_delta is None:
            expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)

        expire = datetime.now(timezone.utc) + expires_delta

        to_encode = {
            "sub": user_id,
            "type": TokenType.REFRESH.value,
            "family_id": family_id,
            "jti": str(uuid4()),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }

        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            Token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            return None

    @staticmethod
    def is_access_token(payload: dict) -> bool:
        """Check if token is an access token."""
        return payload.get("type") == TokenType.ACCESS.value

    @staticmethod
    def is_refresh_token(payload: dict) -> bool:
        """Check if token is a refresh token."""
        return payload.get("type") == TokenType.REFRESH.value

    @staticmethod
    def get_user_id(payload: dict) -> Optional[str]:
        """Extract user ID from token payload."""
        return payload.get("sub")

    @staticmethod
    def is_expired(payload: dict) -> bool:
        """Check if token is expired."""
        exp = payload.get("exp")
        if exp is None:
            return True
        return datetime.now(timezone.utc) > datetime.fromtimestamp(exp, tz=timezone.utc)
