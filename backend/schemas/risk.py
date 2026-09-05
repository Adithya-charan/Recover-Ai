from pydantic import BaseModel, Field


class RiskResult(BaseModel):
    risk_score: int = Field(..., ge=0, le=100, description="Risk score from 0 to 100")
    risk_level: str = Field(..., description="Risk tier: low, medium, high")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    model_version: str = Field("risk-v1", description="Version of the risk evaluation model")
    detected_revenue_at_risk: float = Field(0.0, description="Amount exposed to risk")
