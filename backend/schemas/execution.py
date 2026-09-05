from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    execution_status: str = Field(..., description="Status: EXECUTED, BLOCKED, SIMULATED, NOT_EXECUTED")
    recovery_status: str = Field(..., description="Outcome: RECOVERED, FAILED, FOLLOW_UP, NOT_ATTEMPTED")
    recovered_amount: float = Field(0.0, description="Amount recovered in INR")
    execution_message: str = Field(..., description="Message describing execution attempt or policy block")
