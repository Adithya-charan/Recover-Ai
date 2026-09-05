from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from .transaction import TransactionInput
from .risk import RiskResult
from .decision import AIDecisionResult
from .policy import PolicyResult
from .execution import ExecutionResult


class EligibilityResult(BaseModel):
    eligible: bool = Field(..., description="Whether the transaction is eligible for recovery")
    reason: str = Field(..., description="Reason for recovery eligibility assessment")


class PipelineResult(BaseModel):
    transaction_id: str
    transaction: TransactionInput
    eligibility: EligibilityResult
    risk: RiskResult
    decision: AIDecisionResult
    policy: PolicyResult
    execution: ExecutionResult
    final_status: str = Field(..., description="Overall pipeline outcome: recovered, blocked, follow_up, stopped, failed")
