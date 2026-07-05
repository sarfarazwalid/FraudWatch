"""Fraud Rules API endpoints."""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict
from app.dependencies.auth import get_current_active_user
from app.dependencies.services import FraudRuleService, get_fraud_rule_service
from app.models.identity.user import User
from app.api.response import success_response, pagination_meta

logger = logging.getLogger(__name__)
router = APIRouter(tags=["fraud-rules"])

class FraudRuleResponse(BaseModel):
    id: str; name: str; description: Optional[str] = None; rule_type: str
    severity: str; priority: int; conditions: Optional[dict] = None
    actions: Optional[dict] = None; is_active: bool; is_system_rule: bool
    version: int; created_by: Optional[str] = None; created_at: datetime; updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class FraudRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None; rule_type: str = "rule"
    severity: str = "medium"; priority: int = Field(0, ge=0)
    conditions: Optional[dict] = None; actions: Optional[dict] = None

class FraudRuleUpdate(BaseModel):
    name: Optional[str] = None; description: Optional[str] = None
    severity: Optional[str] = None; priority: Optional[int] = Field(None, ge=0)
    conditions: Optional[dict] = None; actions: Optional[dict] = None
    is_active: Optional[bool] = None

@router.get("/", response_model=dict)
async def list_rules(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("name"), sort_order: str = Query("asc", regex="^(asc|desc)$"),
    search: Optional[str] = Query(None), rule_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None), is_active: Optional[bool] = Query(None),
    rule_service: FraudRuleService = Depends(get_fraud_rule_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        rules, total = await rule_service.list_rules(
            page=page, page_size=page_size, search=search,
            filters={"rule_type": rule_type, "severity": severity, "is_active": is_active},
            sort_by=sort_by, sort_order=sort_order,
        )
        items = [FraudRuleResponse.model_validate(r) for r in rules]
        meta = pagination_meta(page, page_size, total, sort_by, sort_order)
        return success_response(data=items, message=f"Retrieved {len(items)} rules", meta=meta)
    except Exception as e:
        logger.error(f"Error listing rules: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{rule_id}", response_model=dict)
async def get_rule(rule_id: str, rule_service: FraudRuleService = Depends(get_fraud_rule_service), current_user: User = Depends(get_current_active_user)):
    try:
        rule = await rule_service.get_rule(rule_id)
        if not rule: raise HTTPException(status_code=404, detail="Rule not found")
        return success_response(data=FraudRuleResponse.model_validate(rule), message="Rule retrieved")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=dict, status_code=201)
async def create_rule(data: FraudRuleCreate, rule_service: FraudRuleService = Depends(get_fraud_rule_service), current_user: User = Depends(get_current_active_user)):
    try:
        rule = await rule_service.create_rule(data.model_dump(), created_by=str(current_user.id))
        logger.info(f"Rule created by {current_user.id}: {rule.id}")
        return success_response(data=FraudRuleResponse.model_validate(rule), message="Rule created")
    except ValueError as e: raise HTTPException(status_code=409, detail=str(e))
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{rule_id}", response_model=dict)
async def update_rule(rule_id: str, data: FraudRuleUpdate, rule_service: FraudRuleService = Depends(get_fraud_rule_service), current_user: User = Depends(get_current_active_user)):
    try:
        rule = await rule_service.update_rule(rule_id, data.model_dump(exclude_none=True))
        if not rule: raise HTTPException(status_code=404, detail="Rule not found")
        logger.info(f"Rule {rule_id} updated by {current_user.id}")
        return success_response(data=FraudRuleResponse.model_validate(rule), message="Rule updated")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{rule_id}", response_model=dict)
async def deactivate_rule(rule_id: str, rule_service: FraudRuleService = Depends(get_fraud_rule_service), current_user: User = Depends(get_current_active_user)):
    try:
        success = await rule_service.deactivate_rule(rule_id)
        if not success: raise HTTPException(status_code=404, detail="Rule not found")
        logger.info(f"Rule {rule_id} deactivated by {current_user.id}")
        return success_response(message="Rule deactivated")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))
