from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, func

from app.database import Base


class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False)
    hostname = Column(String(128))
    ip = Column(String(64))
    mac = Column(String(64))
    os = Column(String(128))
    cpu = Column(String(64))
    memory = Column(String(64))
    disk = Column(String(64))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    department = Column(String(128))
    plan_id = Column(Integer, ForeignKey("coding_plans.id"), nullable=True)
    openclaw_version = Column(String(64))
    agent_version = Column(String(64))
    status = Column(Enum("online", "offline", "error", "pending_init", "disabled"), default="pending_init")
    last_heartbeat_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AgentInfo(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), unique=True)
    agent_version = Column(String(64))
    install_path = Column(String(256))
    service_status = Column(Enum("running", "stopped", "error"), default="stopped")
    last_report_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class OpenClawConfig(Base):
    __tablename__ = "openclaw_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    config_version = Column(String(64))
    model_provider = Column(String(128))
    model_name = Column(String(128))
    config_json = Column(Text)
    created_at = Column(DateTime, default=func.now())
