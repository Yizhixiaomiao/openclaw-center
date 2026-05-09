from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, func

from app.database import Base


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    level = Column(Enum("debug", "info", "warning", "error", "critical"), default="info")
    category = Column(String(64))
    message = Column(Text)
    detail_json = Column(Text)
    created_at = Column(DateTime, default=func.now())


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)
    scenario_id = Column(Integer, ForeignKey("business_scenarios.id"), nullable=True)
    title = Column(String(256), nullable=False)
    description = Column(Text)
    status = Column(Enum("open", "in_progress", "waiting_user", "resolved", "closed"), default="open")
    owner = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
