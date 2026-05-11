from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class MachineCreate(BaseModel):
    code: str
    hostname: Optional[str] = None
    ip: Optional[str] = None
    mac: Optional[str] = None
    os: Optional[str] = None
    cpu: Optional[str] = None
    memory: Optional[str] = None
    disk: Optional[str] = None
    user_id: Optional[int] = None
    department: Optional[str] = None
    plan_id: Optional[int] = None
    openclaw_version: Optional[str] = None
    agent_version: Optional[str] = None
    current_user: Optional[str] = None


class MachineUpdate(BaseModel):
    hostname: Optional[str] = None
    ip: Optional[str] = None
    mac: Optional[str] = None
    os: Optional[str] = None
    cpu: Optional[str] = None
    memory: Optional[str] = None
    disk: Optional[str] = None
    user_id: Optional[int] = None
    department: Optional[str] = None
    plan_id: Optional[int] = None
    openclaw_version: Optional[str] = None
    agent_version: Optional[str] = None
    status: Optional[str] = None
    current_user: Optional[str] = None


class MachineResponse(BaseModel):
    id: int
    code: str
    hostname: Optional[str] = None
    ip: Optional[str] = None
    mac: Optional[str] = None
    os: Optional[str] = None
    cpu: Optional[str] = None
    memory: Optional[str] = None
    disk: Optional[str] = None
    user_id: Optional[int] = None
    department: Optional[str] = None
    plan_id: Optional[int] = None
    openclaw_version: Optional[str] = None
    agent_version: Optional[str] = None
    status: str
    current_user: Optional[str] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    skills_count: Optional[int] = 0
    last_heartbeat_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentRegisterRequest(BaseModel):
    machine_code: str
    hostname: str
    ip: str
    os: Optional[str] = None
    agent_version: Optional[str] = None
    openclaw_version: Optional[str] = None
    current_user: Optional[str] = None
    agent_config_content: Optional[str] = None
    agent_config_path: Optional[str] = None


class AgentHeartbeatRequest(BaseModel):
    machine_code: str
    status: Optional[str] = None
    agent_version: Optional[str] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    service_status: Optional[str] = None
    current_user: Optional[str] = None
    agent_config_content: Optional[str] = None
    agent_config_path: Optional[str] = None


class AgentConfigReportRequest(BaseModel):
    machine_code: str
    openclaw_config_hash: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    skills: Optional[str] = None  # JSON string
    prompt_versions: Optional[str] = None  # JSON string
    config_content: Optional[str] = None  # Full config file content
    config_file_path: Optional[str] = None  # Full path to config file on agent machine


class AgentTaskReportRequest(BaseModel):
    task_item_id: int
    status: str
    message: Optional[str] = None
    log_excerpt: Optional[str] = None


class AgentLogReportRequest(BaseModel):
    machine_code: str
    level: Optional[str] = "info"
    category: Optional[str] = None
    message: str
    detail_json: Optional[str] = None


class AgentUsageReportRequest(BaseModel):
    machine_code: str
    plan_id: Optional[int] = None
    calls: int = 0
    tokens: int = 0
    timestamp: Optional[str] = None


class AgentSkillSyncRequest(BaseModel):
    machine_code: str
    skills: str  # JSON string of skill packages (code, name, version, description, zip_base64, checksum, file_count, total_size)


class ConfigUpdateRequest(BaseModel):
    config_content: str  # Full JSON config content to save and sync


class AgentConfigUpdateRequest(BaseModel):
    agent_config_content: str  # Full YAML config content for agent