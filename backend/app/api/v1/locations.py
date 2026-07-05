"""Locations API endpoints."""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict
from app.dependencies.auth import get_current_active_user
from app.dependencies.services import LocationService, get_location_service
from app.models.identity.user import User
from app.api.response import success_response, pagination_meta

logger = logging.getLogger(__name__)
router = APIRouter(tags=["locations"])

class LocationResponse(BaseModel):
    id: str; address: Optional[str] = None; city: Optional[str] = None; state: Optional[str] = None
    country: Optional[str] = None; postal_code: Optional[str] = None; latitude: Optional[float] = None
    longitude: Optional[float] = None; location_type: Optional[str] = None; is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class LocationCreate(BaseModel):
    address: Optional[str] = None; city: Optional[str] = None; state: Optional[str] = None
    country: Optional[str] = None; postal_code: Optional[str] = None
    latitude: Optional[float] = None; longitude: Optional[float] = None
    location_type: Optional[str] = None

class LocationUpdate(BaseModel):
    address: Optional[str] = None; city: Optional[str] = None; state: Optional[str] = None
    country: Optional[str] = None; postal_code: Optional[str] = None
    latitude: Optional[float] = None; longitude: Optional[float] = None
    location_type: Optional[str] = None; is_active: Optional[bool] = None

@router.get("/", response_model=dict)
async def list_locations(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"), sort_order: str = Query("desc", regex="^(asc|desc)$"),
    search: Optional[str] = Query(None), country: Optional[str] = Query(None),
    city: Optional[str] = Query(None), location_type: Optional[str] = Query(None),
    location_service: LocationService = Depends(get_location_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        filters = {}
        if country: filters["country"] = country
        if city: filters["city"] = city
        if location_type: filters["location_type"] = location_type
        locations, total = await location_service.list_locations(
            page=page, page_size=page_size, search=search,
            filters=filters if filters else None, sort_by=sort_by, sort_order=sort_order,
        )
        items = [LocationResponse.model_validate(l) for l in locations]
        meta = pagination_meta(page, page_size, total, sort_by, sort_order)
        return success_response(data=items, message=f"Retrieved {len(items)} locations", meta=meta)
    except Exception as e:
        logger.error(f"Error listing locations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{location_id}", response_model=dict)
async def get_location(location_id: str, location_service: LocationService = Depends(get_location_service), current_user: User = Depends(get_current_active_user)):
    try:
        location = await location_service.get_location(location_id)
        if not location: raise HTTPException(status_code=404, detail="Location not found")
        return success_response(data=LocationResponse.model_validate(location), message="Location retrieved")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=dict, status_code=201)
async def create_location(data: LocationCreate, location_service: LocationService = Depends(get_location_service), current_user: User = Depends(get_current_active_user)):
    try:
        location = await location_service.create_location(data.model_dump())
        logger.info(f"Location created by {current_user.id}: {location.id}")
        return success_response(data=LocationResponse.model_validate(location), message="Location created")
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{location_id}", response_model=dict)
async def update_location(location_id: str, data: LocationUpdate, location_service: LocationService = Depends(get_location_service), current_user: User = Depends(get_current_active_user)):
    try:
        location = await location_service.update_location(location_id, data.model_dump(exclude_none=True))
        if not location: raise HTTPException(status_code=404, detail="Location not found")
        logger.info(f"Location {location_id} updated by {current_user.id}")
        return success_response(data=LocationResponse.model_validate(location), message="Location updated")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{location_id}", response_model=dict)
async def deactivate_location(location_id: str, location_service: LocationService = Depends(get_location_service), current_user: User = Depends(get_current_active_user)):
    try:
        success = await location_service.deactivate_location(location_id)
        if not success: raise HTTPException(status_code=404, detail="Location not found")
        logger.info(f"Location {location_id} deactivated by {current_user.id}")
        return success_response(message="Location deactivated")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))
