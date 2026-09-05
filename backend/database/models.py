from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime
from backend.database.database import Base


class TransactionRecordDB(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    customer_id = Column(String)
    amount = Column(Float)
    payment_status = Column(String)
    failure_reason = Column(String)
    attempt_count = Column(Integer)
    days_since_event = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditEventDB(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, index=True)
    risk_level = Column(String)
    risk_score = Column(Integer)
    agent_action = Column(String)
    policy_decision = Column(String)
    execution_status = Column(String)
    recovery_status = Column(String)
    recovered_amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)


class RecoveryCaseDB(Base):
    __tablename__ = "recovery_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, unique=True, index=True)
    case_type = Column(String, index=True)
    customer_id = Column(String, index=True)
    transaction_id = Column(String, index=True, nullable=True)
    invoice_id = Column(String, nullable=True)
    subscription_id = Column(String, nullable=True)
    mandate_id = Column(String, nullable=True)
    amount = Column(Float)
    revenue_at_risk = Column(Float)
    status = Column(String, default="new")
    risk_score = Column(Integer, default=50)
    risk_level = Column(String, default="medium")
    diagnosis = Column(String, nullable=True)
    ai_recommendation = Column(String, default="retry")
    ai_confidence = Column(Float, default=0.8)
    policy_decision = Column(String, default="ALLOW")
    policy_reason = Column(String, nullable=True)
    attempt_count = Column(Integer, default=1)
    max_attempts = Column(Integer, default=3)
    next_action = Column(String, nullable=True)
    escalation_status = Column(String, default="none")
    communication_status = Column(String, default="not_sent")
    execution_status = Column(String, default="not_executed")
    outcome = Column(String, default="pending")
    recovered_amount = Column(Float, default=0.0)
    promise_date = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
