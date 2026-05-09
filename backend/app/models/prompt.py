from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, func

from app.database import Base


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    type = Column(Enum("general", "position", "user_specific"), default="general")
    position_type = Column(String(64))
    scenario_type = Column(String(64))
    content = Column(Text, nullable=False)
    variables_json = Column(Text)
    input_file_requirements = Column(Text)
    output_format_requirements = Column(Text)
    processing_rules = Column(Text)
    exception_rules = Column(Text)
    example_input = Column(Text)
    example_output = Column(Text)
    version = Column(Integer, default=1)
    status = Column(Enum("draft", "under_review", "published", "deprecated"), default="draft")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class UserPrompt(Base):
    __tablename__ = "user_prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    scenario_id = Column(Integer, ForeignKey("business_scenarios.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=True)
    content = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    status = Column(Enum("draft", "testing", "active", "deprecated"), default="draft")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
