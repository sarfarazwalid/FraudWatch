"""Fraud Alerts API endpoints."""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict
from app.dependencies.auth import get_current_active_user
from app.dependencies.services import FraudAlertService, FraudCaseService, get_fraud_alert_service, get_fraud_case_service
from app.models.identity.user import User
from app.api.response import success_response, pagination_meta

logger = logging.getLogger(__name__)
router = APIRouter(tags=["fraud-alerts"])

class FraudAlertResponse(BaseModel):
    id: str; title: str; description: Optional[str] = None; severity: str; status: str
    risk_score: Optional[float] = None; transaction_id: Optional[str] = None
    merchant_id: Optional[str] = None; rule_id: Optional[str] = None
    case_id: Optional[str] = None; assigned_to: Optional[str] = None
    created_by: Optional[str] = None; resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None; metadata: Optional[dict] = None
    created_at: datetime; updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class FraudAlertCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None; severity: str = "medium"
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    transaction_id: Optional[str] = None; merchant_id: Optional[str] = None
    rule_id: Optional[str] = None; metadata: Optional[dict] = None

class FraudAlertUpdate(BaseModel):
    title: Optional[str] = None; description: Optional[str] = None
    severity: Optional[str] = None; status: Optional[str] = None
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    assigned_to: Optional[str] = None; metadata: Optional[dict] = None

@router.get("/", response_model=dict)
async def list_fraud_alerts(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"), sort_order: str = Query("desc", regex="^(asc|desc)$"),
    search: Optional[str] = Query(None), severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None), case_id: Optional[str] = Query(None),
    merchant_id: Optional[str] = Query(None),
    alert_service: FraudAlertService = Depends(get_fraud_alert_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        alerts, total = await alert_service.list_alerts(
            page=page, page_size=page_size, search=search,
            filters={"severity": severity, "status": status, "case_id": case_id, "merchant_id": merchant_id},
            sort_by=sort_by, sort_order=sort_order,
        )
        items = [FraudAlertResponse.model_validate(a) for a in alerts]
        meta = pagination_meta(page, page_size, total, sort_by, sort_order)
        return success_response(data=items, message=f"Retrieved {len(items)} alerts", meta=meta)
    except Exception as e:
        logger.error(f"Error listing alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{alert_id}", response_model=dict)
async def get_fraud_alert(alert_id: str, alert_service: FraudAlertService = Depends(get_fraud_alert_service), current_user: User = Depends(get_current_active_user)):
    try:
        alert = await alert_service.get_alert(alert_id)
        if not alert: raise HTTPException(status_code=404, detail="Alert not found")
        return success_response(data=FraudAlertResponse.model_validate(alert), message="Alert retrieved")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=dict, status_code=201)
async def create_fraud_alert(data: FraudAlertCreate, alert_service: FraudAlertService = Depends(get_fraud_alert_service), current_user: User = Depends(get_current_active_user)):
    try:
        alert = await alert_service.create_alert(data.model_dump(), created_by=str(current_user.id))
        logger.info(f"Alert created by {current_user.id}: {alert.id}")
        return success_response(data=FraudAlertResponse.model_validate(alert), message="Alert created")
    except ValueError as e: raise HTTPException(status_code=409, detail=str(e))
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{alert_id}", response_model=dict)
async def update_fraud_alert(alert_id: str, data: FraudAlertUpdate, alert_service: FraudAlertService = Depends(get_fraud_alert_service), current_user: User = Depends(get_current_active_user)):
    try:
        alert = await alert_service.update_alert(alert_id, data.model_dump(exclude_none=True))
        if not alert: raise HTTPException(status_code=404, detail="Alert not found")
        logger.info(f"Alert {alert_id} updated by {current_user.id}")
        return success_response(data=FraudAlertResponse.model_validate(alert), message="Alert updated")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.post("/{alert_id}/resolve", response_model=dict)
async def resolve_alert(alert_id: str, alert_service: FraudAlertService = Depends(get_fraud_alert_service), current_user: User = Depends(get_current_active_user)):
    try:
        alert = await alert_service.resolve_alert(alert_id, resolved_by=str(current_user.id))
        if not alert: raise HTTPException(status_code=404, detail="Alert not found")
        logger.info(f"Alert {alert_id} resolved by {current_user.id}")
        return success_response(data=FraudAlertResponse.model_validate(alert), message="Alert resolved")
    except HTTPException: raise
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))

@router.post("/{alert_id}/escalate", response_model=dict)
async def escalate_to_case(alert_id: str, case_service: FraudCaseService = Depends(get_fraud_case_service), alert_service: FraudAlertService = Depends(get_fraud_alert_service), current_user: User = Depends(get_current_active_user)):
    try:
        case = await case_service.create_case_from_alert(alert_id, created_by=str(current_user.id))
        logger.info(f"Alert {alert_id} escalated to case {case.id} by {current_user.id}")
        return success_response(data={"case_id": str(case.id)}, message="Alert escalated to case")
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))
    except Exception as e: logger.error(f"Error: {e}", exc_info=True); raise HTTPException(status_code=500, detail=str(e))
