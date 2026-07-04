"""
Authentication schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    remember_me: bool = False


class RegisterRequest(BaseModel):
    """User registration request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    password_confirm: str
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: "UserResponse"


class RefreshRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    new_password_confirm: str


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request schema."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    new_password_confirm: str


class SessionResponse(BaseModel):
    """Session response schema."""
    id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_current: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    username: Optional[str]
    first_name: str
    last_name: str
    full_name: str
    phone_number: Optional[str]
    status: str
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    role_name: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    """User profile response schema."""
    id: str
    email: str
    username: Optional[str]
    first_name: str
    last_name: str
    full_name: str
    phone_number: Optional[str]
    status: str
    is_verified: bool
    last_login: Optional[datetime]
    timezone: str
    language: str
    profile_image_url: Optional[str]
    created_at: datetime
    role: "RoleResponse"
    permissions: list[str]
    
    model_config = ConfigDict(from_attributes=True)


class RoleResponse(BaseModel):
    """Role response schema."""
    id: str
    name: str
    description: Optional[str]
    role_type: str
    is_system_role: bool
    permissions: list["PermissionResponse"] = []
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PermissionResponse(BaseModel):
    """Permission response schema."""
    id: str
    name: str
    description: Optional[str]
    resource: str
    action: str
    
    model_config = ConfigDict(from_attributes=True)


# Forward references update
UserResponse.model_rebuild()
UserProfileResponse.model_rebuild()
RoleResponse.model_rebuild()