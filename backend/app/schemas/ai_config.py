from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class AIConfigCreate(BaseModel):
    name: str
    provider: str  # openai | anthropic | other
    api_url: str
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    is_active: Optional[bool] = False


class AIConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    is_active: Optional[bool] = None


class AIConfigResponse(BaseModel):
    id: int
    name: str
    provider: str
    api_url: str
    has_api_key: bool = False
    model_name: Optional[str] = None
    is_active: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestConnectionRequest(BaseModel):
    api_url: str
    api_key: str
    provider: str
    model_name: Optional[str] = None


class TestConnectionResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    model_info: Optional[str] = None
