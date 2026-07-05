"""Merchants API endpoints."""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict
from app.dependencies.auth import get_current_active_user
from app.dependencies.services import MerchantService, get_merchant_service
from app.models.identity.user import User
from app.api.response import success_response, pagination_meta

logger = logging.getLogger(__name__)
router = APIRouter(tags=["merchants"])

class MerchantResponse(BaseModel):
    id: str; name: str; merchant_code: str; status: str; email: Optional[str] = None
    phone: Optional[str] = None; website: Optional[str] = None; country: Optional[str] = None
    risk_level: Optional[str] = None; is_active: bool; created_at: datetime; updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MerchantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    merchant_code: str = Field(..., min_length=1, max_length=50)
    email: Optional[str] = None; phone: Optional[str] = None; website: Optional[str] = None
    country: Optional[str] = None; risk_level: Optional[str] = None

class MerchantUpdate(BaseModel):
    name: Optional[str] = None; email: Optional[str] = None; phone: Optional[str] = None
    website: Optional[str] = None; country: Optional[str] = None; risk_level: Optional[str] = None
    is_active: Optional[bool] = None

@router.get("/", response_model=dict)
async def list_merchants(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("name"), sort_order: str = Query("asc", regex="^(asc|desc)$"),
    search: Optional[str] = Query(None), status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None), country: Optional[str] = Query(None),
    merchant_service: MerchantService = Depends(get_merchant_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        filters = {}
        if status: filters["status"] = status
        if risk_level: filters["risk_level"] = risk_level
        if country: filters["country"] = country
        merchants, total = await merchant_service.list_merchants(
            page=page, page_size=page_size, search=search,
            filters=filters if filters else None, sort_by=sort_by, sort_order=sort_order,
        )
        items = [MerchantResponse.model_validate(m) for m in merchants]
        meta = pagination_meta(page, page_size, total, sort_by, sort_order)
        return success_response(data=items, message=f"Retrieved {len(items)} merchants", meta=meta)
    except Exception as e:
        logger.error(f"Error listing merchants: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{merchant_id}", response_model=dict)
async def get_merchant(merchant_id: str, merchant_service: MerchantService = Depends(get_merchant_service), current_user: User = Depends(get_current_active_user)):
    try:
        merchant = await merchant_service.get_merchant(merchant_id)
        if not merchant: raise HTTPException(status_code=404, detail="Merchant not found")
        return success_response(data=MerchantResponse.model_validate(merchant), message="Merchant retrieved")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=dict, status_code=201)
async def create_merchant(data: MerchantCreate, merchant_service: MerchantService = Depends(get_merchant_service), current_user: User = Depends(get_current_active_user)):
    try:
        merchant = await merchant_service.create_merchant(data.model_dump())
        logger.info(f"Merchant created by {current_user.id}: {merchant.id}")
        return success_response(data=MerchantResponse.model_validate(merchant), message="Merchant created")
    except ValueError as e: raise HTTPException(status_code=409, detail=str(e))
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{merchant_id}", response_model=dict)
async def update_merchant(merchant_id: str, data: MerchantUpdate, merchant_service: MerchantService = Depends(get_merchant_service), current_user: User = Depends(get_current_active_user)):
    try:
        merchant = await merchant_service.update_merchant(merchant_id, data.model_dump(exclude_none=True))
        if not merchant: raise HTTPException(status_code=404, detail="Merchant not found")
        logger.info(f"Merchant {merchant_id} updated by {current_user.id}")
        return success_response(data=MerchantResponse.model_validate(merchant), message="Merchant updated")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{merchant_id}", response_model=dict)
async def deactivate_merchant(merchant_id: str, merchant_service: MerchantService = Depends(get_merchant_service), current_user: User = Depends(get_current_active_user)):
    try:
        success = await merchant_service.deactivate_merchant(merchant_id)
        if not success: raise HTTPException(status_code=404, detail="Merchant not found")
        logger.info(f"Merchant {merchant_id} deactivated by {current_user.id}")
        return success_response(message="Merchant deactivated")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))
