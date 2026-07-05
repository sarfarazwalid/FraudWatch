"""Permissions API endpoints."""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict
from app.dependencies.auth import get_current_active_user
from app.dependencies.services import PermissionService, get_permission_service
from app.models.identity.user import User
from app.api.response import success_response

logger = logging.getLogger(__name__)
router = APIRouter(tags=["permissions"])

class PermissionResponse(BaseModel):
    id: str; name: str; description: Optional[str] = None; resource: str; action: str
    model_config = ConfigDict(from_attributes=True)

class PermissionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    resource: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=50)

@router.get("/", response_model=dict)
async def list_permissions(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    resource: Optional[str] = Query(None), action: Optional[str] = Query(None),
    permission_service: PermissionService = Depends(get_permission_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        permissions, total = await permission_service.list_permissions(
            page=page, page_size=page_size,
            filters={"resource": resource, "action": action} if resource or action else None,
        )
        items = [PermissionResponse.model_validate(p) for p in permissions]
        return success_response(data=items, message=f"Retrieved {len(items)} permissions",
            meta={"page": page, "page_size": page_size, "total": total, "total_pages": (total + page_size - 1) // page_size if total > 0 else 0})
    except Exception as e:
        logger.error(f"Error listing permissions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{permission_id}", response_model=dict)
async def get_permission(permission_id: str, permission_service: PermissionService = Depends(get_permission_service), current_user: User = Depends(get_current_active_user)):
    try:
        perm = await permission_service.get_permission(permission_id)
        if not perm: raise HTTPException(status_code=404, detail="Permission not found")
        return success_response(data=PermissionResponse.model_validate(perm), message="Permission retrieved")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=dict, status_code=201)
async def create_permission(data: PermissionCreate, permission_service: PermissionService = Depends(get_permission_service), current_user: User = Depends(get_current_active_user)):
    try:
        perm = await permission_service.create_permission(name=data.name, description=data.description, resource=data.resource, action=data.action)
        logger.info(f"Permission created by {current_user.id}: {perm.id}")
        return success_response(data=PermissionResponse.model_validate(perm), message="Permission created")
    except ValueError as e: raise HTTPException(status_code=409, detail=str(e))
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{permission_id}", response_model=dict)
async def delete_permission(permission_id: str, permission_service: PermissionService = Depends(get_permission_service), current_user: User = Depends(get_current_active_user)):
    try:
        success = await permission_service.delete_permission(permission_id)
        if not success: raise HTTPException(status_code=404, detail="Permission not found")
        logger.info(f"Permission {permission_id} deleted by {current_user.id}")
        return success_response(message="Permission deleted")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))
