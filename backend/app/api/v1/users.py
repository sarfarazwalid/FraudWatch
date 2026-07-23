"""
Users API endpoints.

Complete CRUD operations for user management.
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.dependencies.database import get_db_session
from app.dependencies.auth import (
    get_current_user,
    get_current_active_user,
)
from app.dependencies.services import (
    UserService,
    SessionService,
    get_user_service,
    get_session_service,
)
from app.models.identity.user import User
from app.models.enums import UserStatus
from app.api.response import success_response, pagination_meta, error_response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


# Schema definitions
class UserListResponse(BaseModel):
    """User list item schema."""
    id: str
    email: str
    username: Optional[str] = None
    full_name: str
    status: str
    is_verified: bool
    last_login: Optional[datetime] = None
    role_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(BaseModel):
    """User detail schema."""
    id: str
    email: str
    username: Optional[str] = None
    first_name: str
    last_name: str
    full_name: str
    phone_number: Optional[str] = None
    status: str
    is_verified: bool
    last_login: Optional[datetime] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    profile_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    role_name: Optional[str] = None
    permissions: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """User creation schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    role_id: Optional[str] = None


class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    profile_image_url: Optional[str] = None
    status: Optional[UserStatus] = None


class ChangePasswordRequest(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UserFilterParams(BaseModel):
    """User filter parameters."""
    search: Optional[str] = None
    email: Optional[str] = None
    status: Optional[UserStatus] = None
    role_id: Optional[str] = None
    is_verified: Optional[bool] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None


# Endpoints
@router.get("/", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    search: Optional[str] = Query(None, description="Search in email, username, name"),
    status: Optional[UserStatus] = Query(None, description="Filter by status"),
    role_id: Optional[str] = Query(None, description="Filter by role"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    email: Optional[str] = Query(None, description="Filter by email"),
    created_from: Optional[datetime] = Query(None, description="Filter created from date"),
    created_to: Optional[datetime] = Query(None, description="Filter created to date"),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all users with pagination, search, and filters.

    Requires permission: users:read
    """
    try:

        # Build filters
        filters = {}
        if status:
            filters["status"] = status
        if role_id:
            filters["role_id"] = role_id
        if is_verified is not None:
            filters["is_verified"] = is_verified
        if email:
            filters["email"] = email
        if created_from:
            filters["created_from"] = created_from
        if created_to:
            filters["created_to"] = created_to

        # Search
        search_term = search if search else None


        users, total = await user_service.list_users(
            page=page,
            page_size=page_size,
            search=search_term,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Calculate pagination
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        # Build response
        items = [UserListResponse.model_validate(user) for user in users]
        meta = pagination_meta(
            page=page,
            page_size=page_size,
            total=total,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters if filters else None,
        )

        logger.info(f"Listed {len(items)} users (page {page}/{total_pages})")

        return success_response(
            data=items,
            message=f"Retrieved {len(items)} users",
            meta=meta,
        )

    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/me", response_model=dict)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get current user's profile.

    Returns detailed profile of the authenticated user.
    """
    try:
        # Refresh user with relationships
        user = await user_service.get_user_with_role(current_user.id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )


        permissions = []
        if user.role and user.role.permissions:
            permissions = [perm.name for perm in user.role.permissions]

        response_data = {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "status": user.status.value if hasattr(user.status, 'value') else str(user.status),
            "is_verified": user.is_verified,
            "last_login": user.last_login,
            "timezone": user.timezone,
            "language": user.language,
            "profile_image_url": user.profile_image_url,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "role_name": user.role.name if user.role else None,
            "permissions": permissions,
        }

        return success_response(
            data=response_data,
            message="Profile retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.patch("/me", response_model=dict)
async def update_current_user_profile(
    data: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update current user's profile.

    Allows users to update their own profile information.
    """
    try:

        # Convert Pydantic model to dict, excluding None values
        update_data = data.model_dump(exclude_none=True)

        # Remove status from update (users cannot change their own status)
        update_data.pop("status", None)

        # Update user
        updated_user = await user_service.update_user(
            user_id=str(current_user.id),
            **update_data
        )

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        logger.info(f"User {current_user.id} updated their profile")

        return success_response(
            data=UserDetailResponse.model_validate(updated_user),
            message="Profile updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/me/change-password", response_model=dict)
async def change_password(
    data: ChangePasswordRequest,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    Change current user's password.

    Requires current password for verification.
    """
    try:

        # Change password
        success = await user_service.change_password(
            user_id=str(current_user.id),
            current_password=data.current_password,
            new_password=data.new_password,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        logger.info(f"User {current_user.id} changed their password")

        return success_response(
            message="Password changed successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get user by ID.

    Requires permission: users:read
    """
    try:
        user = await user_service.get_user_with_role(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )


        permissions = []
        if user.role and hasattr(user.role, 'permissions') and user.role.permissions:
            permissions = [perm.name for perm in user.role.permissions]

        response_data = {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "status": user.status.value if hasattr(user.status, 'value') else str(user.status),
            "is_verified": user.is_verified,
            "last_login": user.last_login,
            "timezone": getattr(user, 'timezone', None),
            "language": getattr(user, 'language', None),
            "profile_image_url": getattr(user, 'profile_image_url', None),
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "role_name": user.role.name if user.role else None,
            "permissions": permissions,
        }

        return success_response(
            data=response_data,
            message="User retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new user.

    Requires permission: users:create
    """
    try:

        # Check if email already exists
        existing = await user_service.get_user_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

        # Create user
        user = await user_service.create_user(
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            username=data.username,
            phone_number=data.phone_number,
            role_id=data.role_id,
        )

        logger.info(f"User created by {current_user.id}: {user.id}")

        return success_response(
            data=UserDetailResponse.model_validate(user),
            message="User created successfully",
            status_code=status.HTTP_201_CREATED,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.patch("/{user_id}", response_model=dict)
async def update_user(
    user_id: str,
    data: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update user by ID.

    Requires permission: users:update
    """
    try:

        # Check if user exists
        existing = await user_service.get_user(user_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Convert Pydantic model to dict, excluding None values
        update_data = data.model_dump(exclude_none=True)

        # Update user
        updated_user = await user_service.update_user(user_id, **update_data)

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        logger.info(f"User {user_id} updated by {current_user.id}")

        return success_response(
            data=UserDetailResponse.model_validate(updated_user),
            message="User updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/{user_id}", response_model=dict)
async def deactivate_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    Deactivate user (soft delete).

    Requires permission: users:delete
    """
    try:
        # Prevent self-deletion
        if user_id == str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate yourself",
            )
        success = await user_service.deactivate_user(user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        logger.info(f"User {user_id} deactivated by {current_user.id}")

        return success_response(
            message="User deactivated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/sessions/my-sessions", response_model=dict)
async def get_my_sessions(
    session_service: SessionService = Depends(get_session_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current user's active sessions.

    Returns list of active sessions for the authenticated user.
    """
    try:
        sessions = await session_service.get_user_sessions(str(current_user.id))

        return success_response(
            data=sessions,
            message=f"Retrieved {len(sessions)} active sessions",
        )

    except Exception as e:
        logger.error(f"Error getting user sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/sessions/{session_id}", response_model=dict)
async def revoke_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    Revoke a specific session.

    Allows users to revoke their own sessions.
    """
    try:

        # Revoke session
        success = await session_service.revoke_session(session_id, str(current_user.id))

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        logger.info(f"Session {session_id} revoked by user {current_user.id}")

        return success_response(
            message="Session revoked successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
