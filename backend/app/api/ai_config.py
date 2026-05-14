import json
import httpx
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.utils.deps import get_db, get_current_user, require_role
from app.utils.security import encrypt_value, decrypt_value
from app.models.user import User
from app.models.ai_config import AIConfig
from app.schemas.ai_config import (
    AIConfigCreate,
    AIConfigUpdate,
    AIConfigResponse,
    TestConnectionRequest,
    TestConnectionResponse,
)

router = APIRouter()


def _config_to_response(cfg: AIConfig) -> dict:
    data = AIConfigResponse.model_validate(cfg).model_dump()
    data["has_api_key"] = bool(cfg.api_key_encrypted)
    return data


@router.get("/active")
def get_active_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cfg = db.query(AIConfig).filter(AIConfig.is_active == True).first()
    if not cfg:
        return {"item": None}
    return {"item": _config_to_response(cfg)}


@router.post("/test-connection", response_model=TestConnectionResponse)
def test_connection(
    req: TestConnectionRequest,
    current_user: User = Depends(require_role("admin")),
):
    api_url = req.api_url.rstrip("/")
    model = req.model_name or "gpt-3.5-turbo"

    try:
        if req.provider == "anthropic":
            headers = {
                "x-api-key": req.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {
                "model": model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}],
            }
            url = f"{api_url}/messages"
        else:
            headers = {
                "Authorization": f"Bearer {req.api_key}",
                "content-type": "application/json",
            }
            payload = {
                "model": model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}],
            }
            url = f"{api_url}/chat/completions"

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            body = resp.json()

            model_info = model
            if req.provider == "anthropic":
                model_info = body.get("model", model)
            else:
                model_info = body.get("model", model)

            return TestConnectionResponse(success=True, model_info=model_info)

    except httpx.TimeoutException:
        return TestConnectionResponse(success=False, error="连接超时，请检查 API 地址")
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status == 401:
            return TestConnectionResponse(success=False, error="API Key 无效或已过期")
        elif status == 403:
            return TestConnectionResponse(success=False, error="无权访问此 API")
        return TestConnectionResponse(success=False, error=f"API 返回错误 (HTTP {status})")
    except httpx.ConnectError:
        return TestConnectionResponse(success=False, error="无法连接到 API，请检查地址")
    except Exception as e:
        return TestConnectionResponse(success=False, error=f"测试失败: {str(e)}")


@router.get("")
def list_configs(
    provider: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AIConfig)
    if provider:
        q = q.filter(AIConfig.provider == provider)
    total = q.count()
    items = q.order_by(AIConfig.is_active.desc(), AIConfig.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": [_config_to_response(c) for c in items], "total": total}


@router.post("", response_model=AIConfigResponse, status_code=201)
def create_config(
    req: AIConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    data = req.model_dump(exclude={"api_key"})
    if req.api_key:
        data["api_key_encrypted"] = encrypt_value(req.api_key)

    if req.is_active:
        db.query(AIConfig).filter(AIConfig.is_active == True).update({"is_active": False})

    cfg = AIConfig(**data)
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return _config_to_response(cfg)


@router.get("/{config_id}")
def get_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cfg = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    return _config_to_response(cfg)


@router.put("/{config_id}", response_model=AIConfigResponse)
def update_config(
    config_id: int,
    req: AIConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    cfg = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="AI配置不存在")

    update_data = req.model_dump(exclude_unset=True, exclude={"api_key"})
    if req.api_key is not None:
        update_data["api_key_encrypted"] = encrypt_value(req.api_key)

    if update_data.get("is_active"):
        db.query(AIConfig).filter(AIConfig.is_active == True).update({"is_active": False})

    for k, v in update_data.items():
        setattr(cfg, k, v)
    db.commit()
    db.refresh(cfg)
    return _config_to_response(cfg)


@router.delete("/{config_id}")
def delete_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    cfg = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    db.delete(cfg)
    db.commit()
    return {"status": "ok", "message": "AI配置已删除"}


@router.post("/{config_id}/test", response_model=TestConnectionResponse)
def test_config_connection(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    cfg = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    if not cfg.api_key_encrypted:
        return TestConnectionResponse(success=False, error="未配置API Key")

    api_key = decrypt_value(cfg.api_key_encrypted)
    api_url = cfg.api_url.rstrip("/")
    model = cfg.model_name or "gpt-3.5-turbo"

    try:
        if cfg.provider == "anthropic":
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {
                "model": model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}],
            }
            url = f"{api_url}/messages"
        else:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "content-type": "application/json",
            }
            payload = {
                "model": model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}],
            }
            url = f"{api_url}/chat/completions"

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            body = resp.json()
            model_info = body.get("model", model)
            return TestConnectionResponse(success=True, model_info=model_info)

    except httpx.TimeoutException:
        return TestConnectionResponse(success=False, error="连接超时，请检查 API 地址")
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status == 401:
            return TestConnectionResponse(success=False, error="API Key 无效或已过期")
        elif status == 403:
            return TestConnectionResponse(success=False, error="无权访问此 API")
        return TestConnectionResponse(success=False, error=f"API 返回错误 (HTTP {status})")
    except httpx.ConnectError:
        return TestConnectionResponse(success=False, error="无法连接到 API，请检查地址")
    except Exception as e:
        return TestConnectionResponse(success=False, error=f"测试失败: {str(e)}")


@router.post("/{config_id}/set-active", response_model=AIConfigResponse)
def set_active_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    cfg = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="AI配置不存在")

    db.query(AIConfig).filter(AIConfig.is_active == True).update({"is_active": False})
    cfg.is_active = True
    db.commit()
    db.refresh(cfg)
    return _config_to_response(cfg)
