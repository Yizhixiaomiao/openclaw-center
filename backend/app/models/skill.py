from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, func

from app.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    code = Column(String(64), unique=True, nullable=False)
    version = Column(String(32))
    description = Column(Text)
    package_url = Column(String(512))
    checksum = Column(String(128))
    position_type = Column(String(64))
    dependencies = Column(Text)
    config_params = Column(Text)
    entry_command = Column(String(256))
    install_path = Column(String(256))
    test_sample = Column(Text)
    audit_status = Column(Enum("pending", "approved", "rejected"), default="pending")
    status = Column(Enum("draft", "published", "deprecated"), default="draft")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class MachineSkill(Base):
    __tablename__ = "machine_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    skill_id = Column(Integer, ForeignKey("skills.id"))
    installed_version = Column(String(32))
    status = Column(Enum("installed", "installing", "failed", "removed"), default="installed")
    installed_at = Column(DateTime, default=func.now())
