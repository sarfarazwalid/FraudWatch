"""
Roles API endpoints.

Complete CRUD operations for role management.
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict

from app.dependencies.auth import get_current_active_user
from app.dependencies.services import RoleService, get_role_service
from app.models.identity.user import User
from app.api.response import success_response, pagination_meta

logger = logging.getLogger(__name__)

router = APIRouter(tags=["roles"])


class PermissionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    resource: str
    action: str
    model_config = ConfigDict(from_attributes=True)


class RoleListResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    role_type: str
    is_system_role: bool
    is_active: bool
    permission_count: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RoleDetailResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    role_type: str
    is_system_role: bool
    is_active: bool
    permissions: list[PermissionResponse] = []
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    role_type: str = Field(..., max_length=50)
    permission_ids: list[str] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    role_type: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    permission_ids: Optional[list[str]] = None


@router.get("/", response_model=dict)
async def list_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    role_type: Optional[str] = Query(None),
    role_service: RoleService = Depends(get_role_service),
    current_user: User = Depends(get_current_active_user),
):
    """List all roles with pagination."""
    try:
        roles, total = await role_service.list_roles(
            page=page, page_size=page_size, search=search,
            filters={"is_active": is_active, "role_type": role_type} if is_active is not None or role_type else None,
            sort_by=sort_by, sort_order=sort_order,
        )
        items = [RoleListResponse.model_validate(r) for r in roles]
        meta = pagination_meta(page, page_size, total, sort_by, sort_order)
        return success_response(data=items, message=f"Retrieved {len(items)} roles", meta=meta)
    except Exception as e:
        logger.error(f"Error listing roles: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{role_id}", response_model=dict)
async def get_role(
    role_id: str,
    role_service: RoleService = Depends(get_role_service),
    current_user: User = Depends(get_current_active_user),
):
    """Get role by ID."""
    try:
        role = await role_service.get_role_with_permissions(role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return success_response(data=RoleDetailResponse.model_validate(role), message="Role retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting role {role_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleCreate,
    role_service: RoleService = Depends(get_role_service),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new role."""
    try:
        role = await role_service.create_role(
            name=data.name, description=data.description,
            role_type=data.role_type, permission_ids=data.permission_ids,
        )
        logger.info(f"Role created by {current_user.id}: {role.id}")
        return success_response(data=RoleDetailResponse.model_validate(role), message="Role created successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating role: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{role_id}", response_model=dict)
async def update_role(
    role_id: str,
    data: RoleUpdate,
    role_service: RoleService = Depends(get_role_service),
    current_user: User = Depends(get_current_active_user),
):
    """Update role by ID."""
    try:
        role = await role_service.update_role(role_id, **data.model_dump(exclude_none=True))
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        logger.info(f"Role {role_id} updated by {current_user.id}")
        return success_response(data=RoleDetailResponse.model_validate(role), message="Role updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating role {role_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{role_id}", response_model=dict)
async def delete_role(
    role_id: str,
    role_service: RoleService = Depends(get_role_service),
    current_user: User = Depends(get_current_active_user),
):
    """Delete role (soft delete)."""
    try:
        success = await role_service.deactivate_role(role_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        logger.info(f"Role {role_id} deactivated by {current_user.id}")
        return success_response(message="Role deactivated successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating role {role_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
