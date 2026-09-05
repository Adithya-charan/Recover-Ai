from pydantic import BaseModel, Field


class PolicyResult(BaseModel):
    allowed: bool = Field(..., description="Whether the recommended action is permitted by policy")
    policy_status: str = Field(..., description="Status: allowed, blocked")
    reason: str = Field(..., description="Detailed policy evaluation rationale")
