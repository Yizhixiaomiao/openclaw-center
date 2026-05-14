from sqlalchemy import Column, Integer, String, Text, BigInteger, Numeric, Date, DateTime, Enum, ForeignKey, func

from app.database import Base


class CodingPlan(Base):
    __tablename__ = "coding_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(128), nullable=False)
    plan_name = Column(String(128), nullable=False)
    monthly_cost = Column(Numeric(10, 2), default=0)
    quota_type = Column(Enum("calls", "tokens", "unlimited"), default="tokens")
    quota_limit = Column(BigInteger, default=0)
    quota_used = Column(BigInteger, default=0)
    billing_cycle = Column(String(32), default="monthly")
    warning_threshold = Column(Numeric(5, 2), default=80.00)
    status = Column(Enum("active", "expired", "disabled"), default="active")
    api_url = Column(String(512), nullable=True)
    api_key_encrypted = Column(Text, nullable=True)
    supported_models = Column(Text, nullable=True)
    rate_limits = Column(Text, nullable=True)
    balance_info = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class PlanBinding(Base):
    __tablename__ = "plan_bindings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("coding_plans.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)
    weight = Column(Numeric(5, 2), default=1.00)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=func.now())


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    plan_id = Column(Integer, ForeignKey("coding_plans.id"), nullable=True)
    calls = Column(Integer, default=0)
    tokens = Column(Integer, default=0)
    cost_estimate = Column(Numeric(10, 4), default=0)
    occurred_at = Column(DateTime, default=func.now())
