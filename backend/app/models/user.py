from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    username = Column(String(64), unique=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    company = Column(String(128))
    department = Column(String(128))
    position = Column(String(128))
    phone = Column(String(32))
    support_owner = Column(String(64))
    role = Column(Enum("admin", "support", "ops", "manager", "user"), default="user")
    status = Column(Enum("active", "disabled"), default="active")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    duties = Column(Text)
    frequent_files = Column(Text)
    output_reports = Column(Text)
    usage_frequency = Column(Enum("low", "medium", "high", "core"), default="low")
    priority = Column(Enum("low", "medium", "high", "critical"), default="medium")
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class BusinessScenario(Base):
    __tablename__ = "business_scenarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(128), nullable=False)
    scenario_type = Column(
        Enum("planning", "warehouse", "quality", "aftersales", "admin", "marketing", "documentation", "other")
    )
    input_desc = Column(Text)
    output_desc = Column(Text)
    rules = Column(Text)
    input_file_types = Column(String(512))
    output_format = Column(String(512))
    template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=True)
    status = Column(
        Enum("pending", "organized", "prompt_generated", "skill_configured", "testing", "online", "needs_optimization", "paused"),
        default="pending",
    )
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
