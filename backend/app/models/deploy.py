from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, func

from app.database import Base


class DeployTask(Base):
    __tablename__ = "deploy_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(Enum("prompt", "skill", "skill_remove", "config", "model_config"), nullable=False)
    target_type = Column(Enum("machine", "user", "department", "position"), nullable=False)
    target_id = Column(String(128))
    payload_json = Column(Text)
    status = Column(Enum("pending", "in_progress", "completed", "failed", "partial"), default="pending")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DeployTaskItem(Base):
    __tablename__ = "deploy_task_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("deploy_tasks.id"))
    machine_id = Column(Integer, ForeignKey("machines.id"))
    status = Column(Enum("pending", "downloading", "installing", "success", "failed", "rollback"), default="pending")
    message = Column(Text)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
