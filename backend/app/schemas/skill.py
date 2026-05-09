from pydantic import BaseModel, Optional
from datetime import datetime


class SkillCreate(BaseModel):
    name: str
    code: str
    version: Optional[str] = None
    description: Optional[str] = None
    package_url: Optional[str] = None
    checksum: Optional[str] = None
    position_type: Optional[str] = None
    dependencies: Optional[str] = None
    config_params: Optional[str] = None
    entry_command: Optional[str] = None
    install_path: Optional[str] = None
    test_sample: Optional[str] = None


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    package_url: Optional[str] = None
    checksum: Optional[str] = None
    position_type: Optional[str] = None
    dependencies: Optional[str] = None
    config_params: Optional[str] = None
    entry_command: Optional[str] = None
    install_path: Optional[str] = None
    test_sample: Optional[str] = None
    audit_status: Optional[str] = None
    status: Optional[str] = None


class SkillResponse(BaseModel):
    id: int
    name: str
    code: str
    version: Optional[str] = None
    description: Optional[str] = None
    package_url: Optional[str] = None
    checksum: Optional[str] = None
    position_type: Optional[str] = None
    dependencies: Optional[str] = None
    config_params: Optional[str] = None
    entry_command: Optional[str] = None
    install_path: Optional[str] = None
    test_sample: Optional[str] = None
    audit_status: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MachineSkillResponse(BaseModel):
    id: int
    machine_id: int
    skill_id: int
    installed_version: Optional[str] = None
    status: str
    installed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
