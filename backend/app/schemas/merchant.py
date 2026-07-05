from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MerchantBase(BaseModel):
    """Base merchant schema with common fields."""
    merchant_code: str = Field(..., min_length=1, max_length=100)
    merchant_name: str = Field(..., min_length=1, max_length=255)
    merchant_category: Optional[str] = Field(None, max_length=100)
    registration_number: Optional[str] = Field(None, max_length=100)
    business_type: Optional[str] = Field(None, max_length=100)
    risk_rating: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = None
    is_active: bool = True


class MerchantCreate(MerchantBase):
    """Merchant creation schema."""
    pass


class MerchantUpdate(BaseModel):
    """Merchant update schema."""
    merchant_name: Optional[str] = Field(None, min_length=1, max_length=255)
    merchant_category: Optional[str] = Field(None, max_length=100)
    registration_number: Optional[str] = Field(None, max_length=100)
    business_type: Optional[str] = Field(None, max_length=100)
    risk_rating: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = None
    is_active: Optional[bool] = None


class MerchantResponse(MerchantBase):
    """Merchant response schema."""
    id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int = 1

    model_config = ConfigDict(from_attributes=True)


class MerchantListResponse(BaseModel):
    """Merchant list item response."""
    id: str
    merchant_code: str
    merchant_name: str
    business_type: Optional[str]
    risk_rating: Optional[str]
    status: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
