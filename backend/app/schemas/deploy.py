from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class DeployTaskCreate(BaseModel):
    task_type: str  # prompt, skill, config, model_config
    target_type: str  # machine, user, department, position
    target_id: str
    payload_json: str


class DeployTaskResponse(BaseModel):
    id: int
    task_type: str
    target_type: str
    target_id: str
    payload_json: Optional[str] = None
    status: str
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeployTaskItemResponse(BaseModel):
    id: int
    task_id: int
    machine_id: int
    status: str
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True
