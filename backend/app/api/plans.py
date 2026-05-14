import json
import httpx
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.utils.deps import get_db, get_current_user, require_role
from app.utils.security import encrypt_value, decrypt_value
from app.models.user import User
from app.models.plan import CodingPlan, PlanBinding, UsageRecord
from app.schemas.plan import (
    CodingPlanCreate,
    CodingPlanUpdate,
    CodingPlanResponse,
    PlanBindingCreate,
    PlanBindingResponse,
    ApiProbeRequest,
    ApiProbeResponse,
)

router = APIRouter()


def _plan_to_response(plan: CodingPlan) -> dict:
    """Convert a CodingPlan ORM object to a response dict with JSON field deserialization."""
    data = CodingPlanResponse.model_validate(plan).model_dump()
    data["has_api_key"] = bool(plan.api_key_encrypted)
    if plan.supported_models:
        try:
            data["supported_models"] = json.loads(plan.supported_models)
        except (json.JSONDecodeError, TypeError):
            data["supported_models"] = None
    else:
        data["supported_models"] = None
    if plan.rate_limits:
        try:
            data["rate_limits"] = json.loads(plan.rate_limits)
        except (json.JSONDecodeError, TypeError):
            data["rate_limits"] = None
    else:
        data["rate_limits"] = None
    if plan.balance_info:
        try:
            data["balance_info"] = json.loads(plan.balance_info)
        except (json.JSONDecodeError, TypeError):
            data["balance_info"] = None
    else:
        data["balance_info"] = None
    return data


# ---------- Known Anthropic models (fallback) ----------
ANTHROPIC_KNOWN_MODELS = [
    {"id": "claude-opus-4-20250514", "owned_by": "anthropic"},
    {"id": "claude-sonnet-4-20250514", "owned_by": "anthropic"},
    {"id": "claude-haiku-4-20250414", "owned_by": "anthropic"},
    {"id": "claude-3-5-sonnet-20241022", "owned_by": "anthropic"},
    {"id": "claude-3-5-haiku-20241022", "owned_by": "anthropic"},
    {"id": "claude-3-opus-20240229", "owned_by": "anthropic"},
]


@router.post("/probe-api", response_model=ApiProbeResponse)
def probe_api(
    req: ApiProbeRequest,
    current_user: User = Depends(require_role("admin")),
):
    """Probe an external API (OpenAI-compatible or Anthropic) to list models and check connectivity."""
    headers = {}
    api_url = req.api_url.rstrip("/")

    if req.provider == "anthropic":
        headers["x-api-key"] = req.api_key
        headers["anthropic-version"] = "2023-06-01"
        models_url = f"{api_url}/models"
    else:
        # OpenAI-compatible (also works for "other")
        headers["Authorization"] = f"Bearer {req.api_key}"
        models_url = f"{api_url}/models"

    rate_limits_info = None
    balance = None

    try:
        with httpx.Client(timeout=10.0) as client:
            # Fetch models
            resp = client.get(models_url, headers=headers)
            resp.raise_for_status()

            # Extract rate limit headers
            rl_headers = {
                "x-ratelimit-limit-requests": resp.headers.get("x-ratelimit-limit-requests"),
                "x-ratelimit-limit-tokens": resp.headers.get("x-ratelimit-limit-tokens"),
                "x-ratelimit-remaining-requests": resp.headers.get("x-ratelimit-remaining-requests"),
                "x-ratelimit-remaining-tokens": resp.headers.get("x-ratelimit-remaining-tokens"),
            }
            if any(v for v in rl_headers.values()):
                rate_limits_info = {k: v for k, v in rl_headers.items() if v is not None}

            # Parse models from response
            body = resp.json()
            models = []
            if "data" in body and isinstance(body["data"], list):
                for m in body["data"]:
                    models.append({
                        "id": m.get("id", ""),
                        "owned_by": m.get("owned_by", ""),
                    })
            elif isinstance(body, list):
                for m in body:
                    models.append({
                        "id": m.get("id", m.get("name", "")),
                        "owned_by": m.get("owned_by", m.get("organization", "")),
                    })

            # Sort models by id
            models.sort(key=lambda x: x["id"])

            # Try to fetch balance/usage for OpenAI-compatible APIs
            if req.provider == "openai" and "openai.com" in api_url:
                try:
                    billing_resp = client.get(
                        "https://api.openai.com/v1/organization/usage/completions?limit=1",
                        headers=headers,
                        timeout=5.0,
                    )
                    if billing_resp.status_code == 200:
                        balance = billing_resp.json()
                except Exception:
                    pass

            provider_detected = req.provider
            if req.provider == "other":
                # Detect from response
                if models and any("claude" in m["id"].lower() for m in models):
                    provider_detected = "anthropic"
                elif models and any("gpt" in m["id"].lower() or "o1" in m["id"].lower() for m in models):
                    provider_detected = "openai"

            return ApiProbeResponse(
                success=True,
                models=models,
                rate_limits=rate_limits_info,
                balance_info=balance,
                provider_detected=provider_detected,
            )

    except httpx.TimeoutException:
        return ApiProbeResponse(success=False, error="连接超时，请检查 API 地址是否正确")
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status == 401:
            return ApiProbeResponse(success=False, error="API Key 无效或已过期")
        elif status == 403:
            return ApiProbeResponse(success=False, error="无权访问此 API")
        elif status == 404:
            # Anthropic may not support /models — try fallback
            if req.provider == "anthropic":
                return ApiProbeResponse(
                    success=True,
                    models=ANTHROPIC_KNOWN_MODELS,
                    provider_detected="anthropic",
                )
            return ApiProbeResponse(success=False, error=f"API 端点不存在 (HTTP {status})")
        return ApiProbeResponse(success=False, error=f"API 返回错误 (HTTP {status})")
    except httpx.ConnectError:
        return ApiProbeResponse(success=False, error="无法连接到 API，请检查地址")
    except Exception as e:
        return ApiProbeResponse(success=False, error=f"探测失败: {str(e)}")


@router.get("")
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
    total = q.count()
    items = q.order_by(CodingPlan.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": [_plan_to_response(p) for p in items], "total": total}


@router.post("", response_model=CodingPlanResponse, status_code=201)
def create_plan(
    req: CodingPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    data = req.model_dump(exclude={"api_key"})
    # Encrypt API key before storage
    if req.api_key:
        data["api_key_encrypted"] = encrypt_value(req.api_key)
    # Serialize supported_models to JSON
    if req.supported_models is not None:
        data["supported_models"] = json.dumps(req.supported_models)
    plan = CodingPlan(**data)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _plan_to_response(plan)


@router.get("/{plan_id}")
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = db.query(CodingPlan).filter(CodingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return _plan_to_response(plan)


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

    update_data = req.model_dump(exclude_unset=True, exclude={"api_key"})
    # Encrypt API key if provided
    if req.api_key is not None:
        update_data["api_key_encrypted"] = encrypt_value(req.api_key)
    # Serialize supported_models to JSON
    if "supported_models" in update_data and update_data["supported_models"] is not None:
        update_data["supported_models"] = json.dumps(update_data["supported_models"])

    for k, v in update_data.items():
        setattr(plan, k, v)
    db.commit()
    db.refresh(plan)
    return _plan_to_response(plan)


@router.delete("/{plan_id}")
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    plan = db.query(CodingPlan).filter(CodingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.query(PlanBinding).filter(PlanBinding.plan_id == plan_id).delete()
    db.query(UsageRecord).filter(UsageRecord.plan_id == plan_id).delete()
    db.delete(plan)
    db.commit()
    return {"status": "ok", "message": "套餐已删除"}


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
