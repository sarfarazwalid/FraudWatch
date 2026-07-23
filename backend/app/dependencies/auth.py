"""
Authentication dependencies for FastAPI.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.dependencies.database import get_db_session
from app.models.identity.user import User
from app.models.enums import UserStatus
from app.repositories.user import UserRepository
from app.repositories.role import RoleRepository
from app.services.jwt import JWTService


async def get_current_user(
    db_session: AsyncSession = Depends(get_db_session),
    authorization: Optional[str] = Header(None)
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        db_session: Database session
        authorization: Authorization header value

    Returns:
        Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not authorization:
        raise credentials_exception

    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise credentials_exception
    except ValueError:
        raise credentials_exception

    # Decode token
    payload = JWTService.decode_token(token)
    if not payload:
        raise credentials_exception

    # Verify it's an access token
    if not JWTService.is_access_token(payload):
        raise credentials_exception

    # Get user ID
    user_id = JWTService.get_user_id(payload)
    if not user_id:
        raise credentials_exception

    # Get user from database
    user_repo = UserRepository(db_session)
    user = await user_repo.get(user_id)

    if not user:
        raise credentials_exception

    if user.status == UserStatus.LOCKED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.

    Args:
        current_user: Current user from token

    Returns:
        Current user if active

    Raises:
        HTTPException: If user is inactive
    """
    if current_user.status == UserStatus.INACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return current_user


async def require_permission(
    permission_name: Optional[str] = None,
    resource: Optional[str] = None,
    action: Optional[str] = None
):
    """
    Dependency factory for permission checking.

    Args:
        permission_name: Permission name to check
        resource: Resource to check permission for
        action: Action to check permission for

    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db_session: AsyncSession = Depends(get_db_session)
    ) -> User:
        """Check if user has required permission."""
        # Admin can do anything
        if current_user.role and current_user.role.name == "super_admin":
            return current_user

        # Check if user has the permission
        if not current_user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No role assigned"
            )

        # Check permissions
        has_permission = any(
            perm.name == permission_name or (perm.resource == resource and perm.action == action)  # type: ignore
            for perm in current_user.role.permissions
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        return current_user

    return permission_checker


async def require_role(role_name: str):
    """
    Dependency factory for role checking.

    Args:
        role_name: Role name to require

    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        """Check if user has required role."""
        if not current_user.role or current_user.role.name != role_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' required"
            )
        return current_user

    return role_checker
