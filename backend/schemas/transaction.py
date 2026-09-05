from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, Any


class TransactionInput(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction ID")
    customer_id: str = Field(..., description="Unique customer ID")
    amount: float = Field(0.0, description="Transaction amount in INR")
    payment_status: str = Field("failed", description="Status of payment: failed, abandoned, success")
    failure_reason: str = Field("unknown", description="Reason for failure: timeout, network_error, upi_failure, bank_declined, insufficient_funds, unknown")
    attempt_count: int = Field(1, description="Number of attempts made")
    customer_previous_payments: int = Field(0, description="Count of past successful payments by customer")
    customer_previous_failures: int = Field(0, description="Count of past failed payments by customer")
    days_since_event: int = Field(0, description="Days elapsed since the transaction failure")
    subscription_status: str = Field("not_applicable", description="Subscription state: active, expired, cancelled, not_applicable")

    @validator("amount", pre=True)
    def parse_amount(cls, v):
        if v is None or v == "":
            return 0.0
        try:
            val = float(v)
            return max(0.0, val)
        except (ValueError, TypeError):
            return 0.0

    @validator("attempt_count", "customer_previous_payments", "customer_previous_failures", "days_since_event", pre=True)
    def parse_integers(cls, v):
        if v is None or v == "":
            return 0
        try:
            val = int(float(v))
            return max(0, val)
        except (ValueError, TypeError):
            return 0

    @validator("payment_status", pre=True)
    def parse_payment_status(cls, v):
        if not v or not isinstance(v, str):
            return "failed"
        cleaned = v.strip().lower()
        return cleaned if cleaned in ["failed", "abandoned", "success"] else "failed"

    @validator("failure_reason", pre=True)
    def parse_failure_reason(cls, v):
        if not v or not isinstance(v, str):
            return "unknown"
        return v.strip().lower()

    @validator("subscription_status", pre=True)
    def parse_subscription_status(cls, v):
        if not v or not isinstance(v, str):
            return "not_applicable"
        return v.strip().lower()

    @validator("transaction_id", "customer_id", pre=True)
    def parse_strings(cls, v):
        if not v or not isinstance(v, str):
            return "UNKNOWN"
        return str(v).strip()
