"""Devices API endpoints."""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict
from app.dependencies.auth import get_current_active_user
from app.dependencies.services import DeviceService, get_device_service
from app.models.identity.user import User
from app.api.response import success_response, pagination_meta

logger = logging.getLogger(__name__)
router = APIRouter(tags=["devices"])

class DeviceResponse(BaseModel):
    id: str; device_id: str; device_type: Optional[str] = None; os: Optional[str] = None
    browser: Optional[str] = None; ip_address: Optional[str] = None; fingerprint: Optional[str] = None
    is_trusted: bool; is_active: bool; first_seen: Optional[datetime] = None; last_seen: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DeviceCreate(BaseModel):
    device_id: str = Field(..., max_length=255); device_type: Optional[str] = None
    os: Optional[str] = None; browser: Optional[str] = None; ip_address: Optional[str] = None
    fingerprint: Optional[str] = None

class DeviceUpdate(BaseModel):
    device_type: Optional[str] = None; os: Optional[str] = None; browser: Optional[str] = None
    ip_address: Optional[str] = None; is_trusted: Optional[bool] = None; is_active: Optional[bool] = None

@router.get("/", response_model=dict)
async def list_devices(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"), sort_order: str = Query("desc", regex="^(asc|desc)$"),
    search: Optional[str] = Query(None), device_type: Optional[str] = Query(None),
    is_trusted: Optional[bool] = Query(None), is_active: Optional[bool] = Query(None),
    device_service: DeviceService = Depends(get_device_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        filters = {}
        if device_type: filters["device_type"] = device_type
        if is_trusted is not None: filters["is_trusted"] = is_trusted
        if is_active is not None: filters["is_active"] = is_active
        devices, total = await device_service.list_devices(
            page=page, page_size=page_size, search=search,
            filters=filters if filters else None, sort_by=sort_by, sort_order=sort_order,
        )
        items = [DeviceResponse.model_validate(d) for d in devices]
        meta = pagination_meta(page, page_size, total, sort_by, sort_order)
        return success_response(data=items, message=f"Retrieved {len(items)} devices", meta=meta)
    except Exception as e:
        logger.error(f"Error listing devices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{device_id}", response_model=dict)
async def get_device(device_id: str, device_service: DeviceService = Depends(get_device_service), current_user: User = Depends(get_current_active_user)):
    try:
        device = await device_service.get_device(device_id)
        if not device: raise HTTPException(status_code=404, detail="Device not found")
        return success_response(data=DeviceResponse.model_validate(device), message="Device retrieved")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=dict, status_code=201)
async def create_device(data: DeviceCreate, device_service: DeviceService = Depends(get_device_service), current_user: User = Depends(get_current_active_user)):
    try:
        device = await device_service.create_device(data.model_dump())
        logger.info(f"Device created by {current_user.id}: {device.id}")
        return success_response(data=DeviceResponse.model_validate(device), message="Device created")
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{device_id}", response_model=dict)
async def update_device(device_id: str, data: DeviceUpdate, device_service: DeviceService = Depends(get_device_service), current_user: User = Depends(get_current_active_user)):
    try:
        device = await device_service.update_device(device_id, data.model_dump(exclude_none=True))
        if not device: raise HTTPException(status_code=404, detail="Device not found")
        logger.info(f"Device {device_id} updated by {current_user.id}")
        return success_response(data=DeviceResponse.model_validate(device), message="Device updated")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{device_id}", response_model=dict)
async def deactivate_device(device_id: str, device_service: DeviceService = Depends(get_device_service), current_user: User = Depends(get_current_active_user)):
    try:
        success = await device_service.deactivate_device(device_id)
        if not success: raise HTTPException(status_code=404, detail="Device not found")
        logger.info(f"Device {device_id} deactivated by {current_user.id}")
        return success_response(message="Device deactivated")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))
