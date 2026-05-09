from typing import Optional
from pydantic import BaseModel
from datetime import date, datetime


class CodingPlanCreate(BaseModel):
    provider: str
    plan_name: str
    monthly_cost: Optional[float] = 0
    quota_type: Optional[str] = "tokens"
    quota_limit: Optional[int] = 0
    billing_cycle: Optional[str] = "monthly"
    warning_threshold: Optional[float] = 80.0
    status: Optional[str] = "active"


class CodingPlanUpdate(BaseModel):
    provider: Optional[str] = None
    plan_name: Optional[str] = None
    monthly_cost: Optional[float] = None
    quota_type: Optional[str] = None
    quota_limit: Optional[int] = None
    billing_cycle: Optional[str] = None
    warning_threshold: Optional[float] = None
    status: Optional[str] = None


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
