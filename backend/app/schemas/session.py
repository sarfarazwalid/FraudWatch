"""
Session schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class SessionResponse(BaseModel):
    """Session response schema."""
    id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_current: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    """Session list response."""
    sessions: list[SessionResponse]
    total: int