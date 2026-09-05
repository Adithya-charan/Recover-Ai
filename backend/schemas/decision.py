from pydantic import BaseModel, Field


class AIDecisionResult(BaseModel):
    action: str = Field(..., description="Recommended AI action: retry, reminder, escalate, stop")
    diagnosis: str = Field(..., description="High-level diagnosis of transaction status/failure")
    reason: str = Field(..., description="Explanation for the recommended action")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence score between 0.0 and 1.0")
