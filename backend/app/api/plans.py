from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.utils.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.plan import CodingPlan, PlanBinding, UsageRecord
from app.schemas.plan import (
    CodingPlanCreate,
    CodingPlanUpdate,
    CodingPlanResponse,
    PlanBindingCreate,
    PlanBindingResponse,
)

router = APIRouter()


@router.get("", response_model=List[CodingPlanResponse])
def list_plans(
    provider: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(CodingPlan)
    if provider:
        q = q.filter(CodingPlan.provider == provider)
    if status:
        q = q.filter(CodingPlan.status == status)
    return q.order_by(CodingPlan.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=CodingPlanResponse, status_code=201)
def create_plan(
    req: CodingPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    plan = CodingPlan(**req.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/{plan_id}", response_model=CodingPlanResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = db.query(CodingPlan).filter(CodingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.put("/{plan_id}", response_model=CodingPlanResponse)
def update_plan(
    plan_id: int,
    req: CodingPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    plan = db.query(CodingPlan).filter(CodingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(plan, k, v)
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/{plan_id}/bindings", response_model=PlanBindingResponse, status_code=201)
def create_binding(
    plan_id: int,
    req: PlanBindingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    if req.plan_id != plan_id:
        raise HTTPException(status_code=400, detail="Plan ID mismatch")
    binding = PlanBinding(**req.model_dump())
    db.add(binding)
    db.commit()
    db.refresh(binding)
    return binding


@router.get("/{plan_id}/bindings", response_model=List[PlanBindingResponse])
def list_bindings(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(PlanBinding).filter(PlanBinding.plan_id == plan_id).all()


@router.get("/{plan_id}/cost-stats")
def plan_cost_stats(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = db.query(CodingPlan).filter(CodingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    bindings = db.query(PlanBinding).filter(PlanBinding.plan_id == plan_id).all()
    total_usage = db.query(UsageRecord).filter(UsageRecord.plan_id == plan_id).all()
    total_calls = sum(u.calls for u in total_usage)
    total_tokens = sum(u.tokens for u in total_usage)
    usage_pct = (
        (plan.quota_used / plan.quota_limit * 100)
        if plan.quota_limit and plan.quota_limit > 0
        else 0
    )
    return {
        "plan_id": plan_id,
        "plan_name": plan.plan_name,
        "monthly_cost": float(plan.monthly_cost),
        "bound_users": len(bindings),
        "total_calls": total_calls,
        "total_tokens": total_tokens,
        "quota_used": plan.quota_used,
        "quota_limit": plan.quota_limit,
        "usage_percentage": round(usage_pct, 2),
        "warning_threshold": float(plan.warning_threshold),
        "is_warning": usage_pct >= float(plan.warning_threshold),
        "is_high_risk": usage_pct >= 100,
    }
