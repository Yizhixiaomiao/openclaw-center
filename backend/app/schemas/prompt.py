from pydantic import BaseModel, Optional
from datetime import datetime


class PromptTemplateCreate(BaseModel):
    name: str
    type: Optional[str] = "general"
    position_type: Optional[str] = None
    scenario_type: Optional[str] = None
    content: str
    variables_json: Optional[str] = None
    input_file_requirements: Optional[str] = None
    output_format_requirements: Optional[str] = None
    processing_rules: Optional[str] = None
    exception_rules: Optional[str] = None
    example_input: Optional[str] = None
    example_output: Optional[str] = None


class PromptTemplateUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    position_type: Optional[str] = None
    scenario_type: Optional[str] = None
    content: Optional[str] = None
    variables_json: Optional[str] = None
    input_file_requirements: Optional[str] = None
    output_format_requirements: Optional[str] = None
    processing_rules: Optional[str] = None
    exception_rules: Optional[str] = None
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    status: Optional[str] = None


class PromptTemplateResponse(BaseModel):
    id: int
    name: str
    type: str
    position_type: Optional[str] = None
    scenario_type: Optional[str] = None
    content: str
    variables_json: Optional[str] = None
    input_file_requirements: Optional[str] = None
    output_format_requirements: Optional[str] = None
    processing_rules: Optional[str] = None
    exception_rules: Optional[str] = None
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    version: int
    status: str
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserPromptCreate(BaseModel):
    user_id: int
    scenario_id: Optional[int] = None
    template_id: Optional[int] = None
    content: str
    version: Optional[int] = 1


class UserPromptUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None


class UserPromptResponse(BaseModel):
    id: int
    user_id: int
    scenario_id: Optional[int] = None
    template_id: Optional[int] = None
    content: str
    version: int
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
