from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class RecoveryCaseInput(BaseModel):
    model_config = ConfigDict(extra="allow")  # tolerate extra fields from callers

    case_id: Optional[str] = None
    case_type: str = Field(
        ...,
        description="PAYMENT_FAILURE | CHECKOUT_ABANDONMENT | FAILED_SUBSCRIPTION | B2B_RECEIVABLE | MANDATE_FAILURE | PROMISE_TO_PAY"
    )
    customer_id: str
    transaction_id: Optional[str] = None
    invoice_id: Optional[str] = None
    subscription_id: Optional[str] = None
    mandate_id: Optional[str] = None
    amount: float
    currency: Optional[str] = "INR"
    payment_status: Optional[str] = "failed"
    failure_reason: Optional[str] = None
    attempt_count: Optional[int] = 1
    max_attempts: Optional[int] = 3
    days_since_event: Optional[int] = 0
    days_overdue: Optional[int] = 0
    promise_date: Optional[str] = None
    customer_previous_payments: Optional[int] = 3
    customer_previous_failures: Optional[int] = 1
    subscription_status: Optional[str] = "active"
    revenue_at_risk: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class RecoveryCaseResult(BaseModel):
    case_id: str
    case_type: str
    customer_id: str
    transaction_id: Optional[str] = None
    amount: float
    revenue_at_risk: float
    status: str
    risk_score: int
    risk_level: str
    diagnosis: str
    ai_recommendation: str
    ai_confidence: float
    policy_decision: str
    policy_reason: str
    attempt_count: int
    max_attempts: int
    next_action: str
    escalation_status: str
    communication_status: str
    execution_status: str
    outcome: str
    recovered_amount: float
    promise_date: Optional[str] = None
    executed_at: Optional[str] = None


class CaseTypeMetrics(BaseModel):
    case_type: str
    total_cases: int
    revenue_at_risk: float
    eligible_cases: int
    recovery_attempts: int
    successful_recoveries: int
    recovered_amount: float
    recovery_rate: float
    blocked_actions: int
    escalated_cases: int
    failed_recovery_cases: int


class BatchMetricsResult(BaseModel):
    total_cases: int
    total_revenue_at_risk: float
    total_eligible_cases: int
    total_recovery_attempts: int
    total_successful_recoveries: int
    total_recovered_amount: float
    overall_recovery_rate: float
    total_blocked_actions: int
    total_escalated_cases: int
    case_type_breakdown: List[CaseTypeMetrics]
