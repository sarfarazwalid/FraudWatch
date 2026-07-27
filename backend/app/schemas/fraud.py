"""
Fraud detection schemas for FraudWatch API.

Defines request/response models for fraud analysis workflow.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FraudAnalysisRequest(BaseModel):
    """Request schema for transaction fraud analysis."""
    amount: float = Field(..., gt=0, description="Transaction amount")
    transaction_type: str = Field(..., description="Transaction type code")
    channel: str = Field(..., description="Transaction channel")
    currency: str = Field(default="USD", description="Currency code")
    sender_identifier: Optional[str] = Field(None, description="Sender account/identifier")
    receiver_identifier: Optional[str] = Field(None, description="Receiver account/identifier")
    merchant_id: Optional[str] = Field(None, description="Merchant ID")
    device_id: Optional[str] = Field(None, description="Device fingerprint")
    location_id: Optional[str] = Field(None, description="Location/country code")
    transaction_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class RuleEvaluationResult(BaseModel):
    """Result of a single rule evaluation."""
    rule_name: str = Field(..., description="Name of the rule")
    triggered: bool = Field(..., description="Whether rule was triggered")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    explanation: str = Field(..., description="Human-readable explanation")


class RuleEvaluationResponse(BaseModel):
    """Response containing all rule evaluation results."""
    rules: List[RuleEvaluationResult] = Field(default_factory=list)
    total_rules: int = Field(0, description="Total rules evaluated")
    triggered_count: int = Field(0, description="Number of triggered rules")
    max_severity: str = Field("none", description="Highest severity among triggered rules")


class FeatureImportance(BaseModel):
    """Feature importance for prediction explanation."""
    amount: float = Field(default=0.0, ge=0, le=1)
    velocity: float = Field(default=0.0, ge=0, le=1)
    device: float = Field(default=0.0, ge=0, le=1)
    location: float = Field(default=0.0, ge=0, le=1)
    merchant: float = Field(default=0.0, ge=0, le=1)


class PredictionResponse(BaseModel):
    """Response from fraud prediction service."""
    model_config = {"protected_namespaces": ()}
    risk_score: float = Field(..., ge=0, le=1)
    prediction: str = Field(..., description="fraud or legitimate")
    confidence: float = Field(..., ge=0, le=1)
    model_version: str = Field(..., description="Model version identifier")
    feature_importance: FeatureImportance = Field(default_factory=FeatureImportance)


class ExplanationResponse(BaseModel):
    """Response for prediction explanation."""
    transaction_id: str = Field(..., description="Transaction UUID")
    risk_score: float = Field(..., ge=0, le=1)
    decision: str = Field(..., description="Final decision: approve, review, reject")
    reasons: List[str] = Field(default_factory=list, description="Human-readable reasons")
    feature_importance: FeatureImportance = Field(default_factory=FeatureImportance)


class AlertResponse(BaseModel):
    """Fraud alert response."""
    id: str
    alert_number: str
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    risk_score: Optional[float] = None
    triggered_rules: List[str] = Field(default_factory=list)
    transaction_id: str
    merchant_id: Optional[str] = None
    rule_id: Optional[str] = None
    case_id: Optional[str] = None
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class CaseResponse(BaseModel):
    """Fraud case response."""
    id: str
    case_number: str
    title: Optional[str] = None
    description: Optional[str] = None
    status: str
    severity: str
    risk_score: Optional[float] = None
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None
    alert_id: Optional[str] = None
    transaction_id: Optional[str] = None
    merchant_id: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class FraudAnalysisResponse(BaseModel):
    """Complete response from transaction fraud analysis."""
    transaction: Dict[str, Any] = Field(..., description="Created transaction data")
    prediction: PredictionResponse = Field(..., description="Fraud prediction result")
    rule_evaluations: RuleEvaluationResponse = Field(..., description="Rule evaluation results")
    alert: Optional[AlertResponse] = Field(None, description="Created alert (if risk >= 0.7)")
    case: Optional[CaseResponse] = Field(None, description="Created case (if risk >= 0.85)")
