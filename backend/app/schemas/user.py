"""
User schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """User update schema."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    profile_image_url: Optional[str] = None


class UserResponse(UserBase):
    """User response schema."""
    id: str
    status: str
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    role_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(UserBase):
    """User profile response with full details."""
    id: str
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


class UserListResponse(BaseModel):
    """User list item response."""
    id: str
    email: str
    username: Optional[str]
    full_name: str
    status: str
    is_verified: bool
    last_login: Optional[datetime]
    role_name: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)