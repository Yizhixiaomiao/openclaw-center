from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class UserCreate(BaseModel):
    name: str
    username: str
    password: str
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    support_owner: Optional[str] = None
    role: Optional[str] = "user"


class UserUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    support_owner: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class UserProfileUpdate(BaseModel):
    duties: Optional[str] = None
    frequent_files: Optional[str] = None
    output_reports: Optional[str] = None
    usage_frequency: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    username: str
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    support_owner: Optional[str] = None
    role: str
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    duties: Optional[str] = None
    frequent_files: Optional[str] = None
    output_reports: Optional[str] = None
    usage_frequency: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ScenarioCreate(BaseModel):
    user_id: int
    name: str
    scenario_type: Optional[str] = None
    input_desc: Optional[str] = None
    output_desc: Optional[str] = None
    rules: Optional[str] = None
    input_file_types: Optional[str] = None
    output_format: Optional[str] = None
    template_id: Optional[int] = None


class ScenarioUpdate(BaseModel):
    name: Optional[str] = None
    scenario_type: Optional[str] = None
    input_desc: Optional[str] = None
    output_desc: Optional[str] = None
    rules: Optional[str] = None
    input_file_types: Optional[str] = None
    output_format: Optional[str] = None
    template_id: Optional[int] = None
    status: Optional[str] = None


class ScenarioResponse(BaseModel):
    id: int
    user_id: int
    name: str
    scenario_type: Optional[str] = None
    input_desc: Optional[str] = None
    output_desc: Optional[str] = None
    rules: Optional[str] = None
    input_file_types: Optional[str] = None
    output_format: Optional[str] = None
    template_id: Optional[int] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
