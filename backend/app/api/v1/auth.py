"""
Authentication API endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.dependencies.services import get_auth_service as get_auth
from app.dependencies.auth import get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, RefreshRequest, UserResponse
from app.models.identity.user import User

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    auth_service = Depends(get_auth)
):
    """
    Register a new user.
    
    Returns:
        TokenResponse with access and refresh tokens
    """
    try:
        user, message = await auth_service.register(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            username=request.username,
            phone_number=request.phone_number
        )
        
        # Auto-login after registration
        token_response = await auth_service.login(
            email=request.email,
            password=request.password
        )
        
        return token_response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    auth_service = Depends(get_auth)
):
    """
    Login user and return tokens.
    
    Returns:
        TokenResponse with access and refresh tokens
    """
    token_response = await auth_service.login(
        email=request.email,
        password=request.password
    )
    
    if not token_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    return token_response


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    auth_service = Depends(get_auth)
):
    """
    Refresh access token using refresh token.
    
    Returns:
        TokenResponse with new access and refresh tokens
    """
    token_response = await auth_service.refresh_access_token(request.refresh_token)
    
    if not token_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    return token_response


@router.post("/logout")
async def logout(
    auth_service = Depends(get_auth)
):
    """
    Logout user by revoking all tokens.
    
    Returns:
        Success message
    """
    # Note: In a real implementation, you'd get the user from the current token
    # For now, this is a placeholder
    return {"message": "Logout endpoint - implement with auth middleware"}


class ChangePasswordRequest(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user profile.
    
    Returns:
        User profile data
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,
        phone_number=current_user.phone_number,
        status=current_user.status.value if hasattr(current_user.status, 'value') else str(current_user.status),
        is_verified=current_user.is_verified,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        role_name=current_user.role.name if current_user.role else None,
    )


@router.post("/change-password")
async def change_password():
    """Change password endpoint."""
    return {"message": "Change password endpoint - implement with auth middleware"}
