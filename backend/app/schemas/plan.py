from typing import Optional, List
from pydantic import BaseModel
from datetime import date, datetime


class ApiProbeRequest(BaseModel):
    api_url: str
    api_key: str
    provider: str  # "openai" | "anthropic" | "other"


class ApiProbeResponse(BaseModel):
    success: bool
    models: List[dict] = []
    rate_limits: Optional[dict] = None
    balance_info: Optional[dict] = None
    error: Optional[str] = None
    provider_detected: Optional[str] = None


class CodingPlanCreate(BaseModel):
    provider: str
    plan_name: str
    monthly_cost: Optional[float] = 0
    quota_type: Optional[str] = "tokens"
    quota_limit: Optional[int] = 0
    billing_cycle: Optional[str] = "monthly"
    warning_threshold: Optional[float] = 80.0
    status: Optional[str] = "active"
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    supported_models: Optional[List[str]] = None


class CodingPlanUpdate(BaseModel):
    provider: Optional[str] = None
    plan_name: Optional[str] = None
    monthly_cost: Optional[float] = None
    quota_type: Optional[str] = None
    quota_limit: Optional[int] = None
    quota_used: Optional[int] = None
    billing_cycle: Optional[str] = None
    warning_threshold: Optional[float] = None
    status: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    supported_models: Optional[List[str]] = None


class CodingPlanResponse(BaseModel):
    id: int
    provider: str
    plan_name: str
    monthly_cost: Optional[float] = None
    quota_type: Optional[str] = None
    quota_limit: Optional[int] = None
    quota_used: Optional[int] = None
    billing_cycle: Optional[str] = None
    warning_threshold: Optional[float] = None
    status: str
    api_url: Optional[str] = None
    has_api_key: Optional[bool] = False
    supported_models: Optional[List[str]] = None
    rate_limits: Optional[dict] = None
    balance_info: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PlanBindingCreate(BaseModel):
    plan_id: int
    user_id: int
    machine_id: Optional[int] = None
    weight: Optional[float] = 1.0
    start_date: date
    end_date: Optional[date] = None


class PlanBindingResponse(BaseModel):
    id: int
    plan_id: int
    user_id: int
    machine_id: Optional[int] = None
    weight: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
