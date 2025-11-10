"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============ Classification Schemas ============
class ClassificationBase(BaseModel):
    criticality: str
    rationale: Optional[str] = None
    model_version: str


class ClassificationResponse(ClassificationBase):
    id: int
    alert_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ User Action Schemas ============
class UserActionBase(BaseModel):
    action: str
    note: Optional[str] = None
    actor: Optional[str] = None


class UserActionCreate(BaseModel):
    note: Optional[str] = None


class UserActionResponse(UserActionBase):
    id: int
    alert_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Alert Schemas ============
class AlertBase(BaseModel):
    source: str
    title: str
    summary: Optional[str] = None
    event_type: Optional[str] = None
    severity: Optional[str] = None
    urgency: Optional[str] = None
    area: Optional[str] = None
    effective_at: datetime
    expires_at: Optional[datetime] = None
    url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AlertCreate(AlertBase):
    natural_key: str
    provider_id: Optional[str] = None
    raw_payload: Optional[str] = None


class AlertResponse(AlertBase):
    id: int
    natural_key: str
    provider_id: Optional[str] = None
    created_at: datetime
    
    # Include latest classification if available
    latest_classification: Optional[ClassificationResponse] = None
    
    # Include user actions
    user_actions: List[UserActionResponse] = []
    
    class Config:
        from_attributes = True


class AlertDetailResponse(AlertResponse):
    """Extended response for detail view including raw payload."""
    raw_payload: Optional[str] = None


class AlertListResponse(BaseModel):
    """Paginated list of alerts."""
    alerts: List[AlertResponse]
    total: int
    page: int
    limit: int
    has_more: bool


# ============ Health Check ============
class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str
    version: str = "0.1.0"

