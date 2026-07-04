"""Transaction DTOs."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.enums import TransactionChannel, SourceSystem

class TransactionBase(BaseModel):
    transaction_reference: str = Field(..., min_length=1, max_length=100)
    external_reference: Optional[str] = None
    sender_identifier: Optional[str] = None
    receiver_identifier: Optional[str] = None
    merchant_id: Optional[str] = None
    agent_id: Optional[str] = None
    device_id: Optional[str] = None
    location_id: Optional[str] = None
    currency_id: str
    payment_method_id: str
    transaction_type_id: str
    status_id: str
    risk_level_id: Optional[str] = None
    amount: float = Field(..., gt=0)
    fee: float = Field(default=0.0, ge=0)
    net_amount: float = Field(..., gt=0)
    exchange_rate: Optional[float] = None
    transaction_timestamp: datetime
    channel: Optional[TransactionChannel] = None
    source_system: Optional[SourceSystem] = None
    description: Optional[str] = None
    transaction_metadata: Optional[Dict[str, Any]] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    transaction_reference: Optional[str] = None
    external_reference: Optional[str] = None
    sender_identifier: Optional[str] = None
    receiver_identifier: Optional[str] = None
    merchant_id: Optional[str] = None
    agent_id: Optional[str] = None
    device_id: Optional[str] = None
    location_id: Optional[str] = None
    currency_id: Optional[str] = None
    payment_method_id: Optional[str] = None
    transaction_type_id: Optional[str] = None
    status_id: Optional[str] = None
    risk_level_id: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    fee: Optional[float] = Field(None, ge=0)
    net_amount: Optional[float] = Field(None, gt=0)
    exchange_rate: Optional[float] = None
    transaction_timestamp: Optional[datetime] = None
    channel: Optional[TransactionChannel] = None
    source_system: Optional[SourceSystem] = None
    description: Optional[str] = None
    transaction_metadata: Optional[Dict[str, Any]] = None

class TransactionInDB(TransactionBase):
    id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    version: int = 1

class TransactionResponse(TransactionBase):
    id: str
    created_at: datetime
    updated_at: datetime
    version: int = 1
    merchant_name: Optional[str] = None
    payment_method_name: Optional[str] = None
    transaction_type_name: Optional[str] = None
    status_name: Optional[str] = None
    risk_level_name: Optional[str] = None

class TransactionFilters(BaseModel):
    search: Optional[str] = None
    merchant_id: Optional[str] = None
    status_id: Optional[str] = None
    risk_level_id: Optional[str] = None
    payment_method_id: Optional[str] = None
    transaction_type_id: Optional[str] = None
    device_id: Optional[str] = None
    location_id: Optional[str] = None
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    channel: Optional[TransactionChannel] = None
    source_system: Optional[SourceSystem] = None
    sort_by: str = "transaction_timestamp"
    sort_order: str = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)

class TransactionStatistics(BaseModel):
    total_transactions: int
    total_volume: float
    average_amount: float
    median_amount: float
    max_amount: float
    min_amount: float
    success_rate: float
    failure_rate: float
    completed_count: int
    failed_count: int
    pending_count: int
    flagged_count: int
    by_payment_method: Dict[str, int]
    by_hour: Dict[int, int]