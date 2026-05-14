from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, func

from app.database import Base


class AIConfig(Base):
    __tablename__ = "ai_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    provider = Column(String(64), nullable=False)  # openai | anthropic | other
    api_url = Column(String(512), nullable=False)
    api_key_encrypted = Column(Text, nullable=True)
    model_name = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
