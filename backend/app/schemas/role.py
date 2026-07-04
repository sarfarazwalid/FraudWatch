"""
Role schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PermissionBase(BaseModel):
    """Base permission schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    resource: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=50)


class PermissionCreate(PermissionBase):
    """Permission creation schema."""
    pass


class PermissionResponse(PermissionBase):
    """Permission response schema."""
    id: str

    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    role_type: str = Field(..., max_length=50)


class RoleCreate(RoleBase):
    """Role creation schema."""
    permission_ids: list[str] = []


class RoleUpdate(BaseModel):
    """Role update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    role_type: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    permission_ids: Optional[list[str]] = None


class RoleResponse(RoleBase):
    """Role response schema."""
    id: str
    is_system_role: bool
    is_active: bool
    permissions: list[PermissionResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoleListResponse(BaseModel):
    """Role list item response."""
    id: str
    name: str
    description: Optional[str]
    role_type: str
    is_system_role: bool
    is_active: bool
    permission_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)