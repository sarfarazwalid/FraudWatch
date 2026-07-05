"""Model Registry API endpoints."""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict
from app.dependencies.auth import get_current_active_user
from app.dependencies.services import ModelRegistryService, get_model_registry_service
from app.models.identity.user import User
from app.api.response import success_response, pagination_meta

logger = logging.getLogger(__name__)
router = APIRouter(tags=["model-registry"])

class ModelRegistryResponse(BaseModel):
    id: str; name: str; version: str; description: Optional[str] = None
    model_type: str; status: str; framework: Optional[str] = None
    accuracy: Optional[float] = None; precision: Optional[float] = None
    recall: Optional[float] = None; f1_score: Optional[float] = None
    is_active: bool; created_by: Optional[str] = None; created_at: datetime; updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ModelRegistryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    version: str = "1.0.0"; description: Optional[str] = None
    model_type: str = "fraud_detection"; framework: Optional[str] = None

class ModelRegistryUpdate(BaseModel):
    description: Optional[str] = None; status: Optional[str] = None
    accuracy: Optional[float] = None; precision: Optional[float] = None
    recall: Optional[float] = None; f1_score: Optional[float] = None
    is_active: Optional[bool] = None

@router.get("/", response_model=dict)
async def list_models(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"), sort_order: str = Query("desc", regex="^(asc|desc)$"),
    search: Optional[str] = Query(None), model_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None), is_active: Optional[bool] = Query(None),
    model_service: ModelRegistryService = Depends(get_model_registry_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        models, total = await model_service.list_models(
            page=page, page_size=page_size, search=search,
            filters={"model_type": model_type, "status": status, "is_active": is_active},
            sort_by=sort_by, sort_order=sort_order,
        )
        items = [ModelRegistryResponse.model_validate(m) for m in models]
        meta = pagination_meta(page, page_size, total, sort_by, sort_order)
        return success_response(data=items, message=f"Retrieved {len(items)} models", meta=meta)
    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_id}", response_model=dict)
async def get_model(model_id: str, model_service: ModelRegistryService = Depends(get_model_registry_service), current_user: User = Depends(get_current_active_user)):
    try:
        model = await model_service.get_model(model_id)
        if not model: raise HTTPException(status_code=404, detail="Model not found")
        return success_response(data=ModelRegistryResponse.model_validate(model), message="Model retrieved")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=dict, status_code=201)
async def create_model(data: ModelRegistryCreate, model_service: ModelRegistryService = Depends(get_model_registry_service), current_user: User = Depends(get_current_active_user)):
    try:
        model = await model_service.create_model(data.model_dump(), created_by=str(current_user.id))
        logger.info(f"Model created by {current_user.id}: {model.id}")
        return success_response(data=ModelRegistryResponse.model_validate(model), message="Model created")
    except ValueError as e: raise HTTPException(status_code=409, detail=str(e))
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{model_id}", response_model=dict)
async def update_model(model_id: str, data: ModelRegistryUpdate, model_service: ModelRegistryService = Depends(get_model_registry_service), current_user: User = Depends(get_current_active_user)):
    try:
        model = await model_service.update_model(model_id, data.model_dump(exclude_none=True))
        if not model: raise HTTPException(status_code=404, detail="Model not found")
        logger.info(f"Model {model_id} updated by {current_user.id}")
        return success_response(data=ModelRegistryResponse.model_validate(model), message="Model updated")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.post("/{model_id}/deploy", response_model=dict)
async def deploy_model(model_id: str, model_service: ModelRegistryService = Depends(get_model_registry_service), current_user: User = Depends(get_current_active_user)):
    try:
        model = await model_service.deploy_model(model_id)
        if not model: raise HTTPException(status_code=404, detail="Model not found")
        logger.info(f"Model {model_id} deployed by {current_user.id}")
        return success_response(data=ModelRegistryResponse.model_validate(model), message="Model deployed")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.post("/{model_id}/archive", response_model=dict)
async def archive_model(model_id: str, model_service: ModelRegistryService = Depends(get_model_registry_service), current_user: User = Depends(get_current_active_user)):
    try:
        model = await model_service.archive_model(model_id)
        if not model: raise HTTPException(status_code=404, detail="Model not found")
        logger.info(f"Model {model_id} archived by {current_user.id}")
        return success_response(data=ModelRegistryResponse.model_validate(model), message="Model archived")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))
