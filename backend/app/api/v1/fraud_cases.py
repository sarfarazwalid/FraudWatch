"""Fraud Cases API endpoints."""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict
from app.dependencies.auth import get_current_active_user
from app.dependencies.services import FraudCaseService, InvestigationTimelineService, get_fraud_case_service, get_investigation_timeline_service
from app.models.identity.user import User
from app.api.response import success_response, pagination_meta

logger = logging.getLogger(__name__)
router = APIRouter(tags=["fraud-cases"])

class FraudCaseResponse(BaseModel):
    id: str; case_number: str; title: str; description: Optional[str] = None
    status: str; severity: str; risk_score: Optional[float] = None
    assigned_to: Optional[str] = None; created_by: Optional[str] = None
    alert_id: Optional[str] = None; transaction_id: Optional[str] = None
    merchant_id: Optional[str] = None; resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None; metadata: Optional[dict] = None
    created_at: datetime; updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class FraudCaseUpdate(BaseModel):
    title: Optional[str] = None; description: Optional[str] = None
    status: Optional[str] = None; severity: Optional[str] = None
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    assigned_to: Optional[str] = None; metadata: Optional[dict] = None

class TimelineEntryCreate(BaseModel):
    action: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    performed_by: Optional[str] = None

@router.get("/", response_model=dict)
async def list_cases(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"), sort_order: str = Query("desc", regex="^(asc|desc)$"),
    search: Optional[str] = Query(None), status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None), assigned_to: Optional[str] = Query(None),
    merchant_id: Optional[str] = Query(None),
    case_service: FraudCaseService = Depends(get_fraud_case_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        cases, total = await case_service.list_cases(
            page=page, page_size=page_size, search=search,
            filters={"status": status, "severity": severity, "assigned_to": assigned_to, "merchant_id": merchant_id},
            sort_by=sort_by, sort_order=sort_order,
        )
        items = [FraudCaseResponse.model_validate(c) for c in cases]
        meta = pagination_meta(page, page_size, total, sort_by, sort_order)
        return success_response(data=items, message=f"Retrieved {len(items)} cases", meta=meta)
    except Exception as e:
        logger.error(f"Error listing cases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{case_id}", response_model=dict)
async def get_case(case_id: str, case_service: FraudCaseService = Depends(get_fraud_case_service), current_user: User = Depends(get_current_active_user)):
    try:
        case = await case_service.get_case(case_id)
        if not case: raise HTTPException(status_code=404, detail="Case not found")
        return success_response(data=FraudCaseResponse.model_validate(case), message="Case retrieved")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{case_id}", response_model=dict)
async def update_case(case_id: str, data: FraudCaseUpdate, case_service: FraudCaseService = Depends(get_fraud_case_service), current_user: User = Depends(get_current_active_user)):
    try:
        case = await case_service.update_case(case_id, data.model_dump(exclude_none=True))
        if not case: raise HTTPException(status_code=404, detail="Case not found")
        logger.info(f"Case {case_id} updated by {current_user.id}")
        return success_response(data=FraudCaseResponse.model_validate(case), message="Case updated")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.post("/{case_id}/resolve", response_model=dict)
async def resolve_case(case_id: str, case_service: FraudCaseService = Depends(get_fraud_case_service), current_user: User = Depends(get_current_active_user)):
    try:
        case = await case_service.resolve_case(case_id, resolved_by=str(current_user.id))
        if not case: raise HTTPException(status_code=404, detail="Case not found")
        logger.info(f"Case {case_id} resolved by {current_user.id}")
        return success_response(data=FraudCaseResponse.model_validate(case), message="Case resolved")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.get("/{case_id}/timeline", response_model=dict)
async def get_case_timeline(case_id: str, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    timeline_service: InvestigationTimelineService = Depends(get_investigation_timeline_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        entries = await timeline_service.get_case_timeline(case_id)
        return success_response(data=entries, message=f"Retrieved {len(entries)} timeline entries")
    except Exception as e:
        logger.error(f"Error getting timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{case_id}/timeline", response_model=dict, status_code=201)
async def add_timeline_entry(case_id: str, data: TimelineEntryCreate,
    timeline_service: InvestigationTimelineService = Depends(get_investigation_timeline_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        entry = await timeline_service.add_entry(
            case_id=case_id, action=data.action, description=data.description,
            performed_by=data.performed_by or str(current_user.id),
        )
        logger.info(f"Timeline entry added to case {case_id} by {current_user.id}")
        return success_response(data=entry, message="Timeline entry added")
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.post("/{case_id}/assign", response_model=dict)
async def assign_case(case_id: str, assigned_to: str = Query(...),
    case_service: FraudCaseService = Depends(get_fraud_case_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        case = await case_service.assign_case(case_id, assigned_to)
        if not case: raise HTTPException(status_code=404, detail="Case not found")
        logger.info(f"Case {case_id} assigned to {assigned_to} by {current_user.id}")
        return success_response(data=FraudCaseResponse.model_validate(case), message="Case assigned")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))
