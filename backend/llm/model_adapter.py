import os
import json
from typing import Union, Dict, Any, Optional
from backend.schemas.transaction import TransactionInput
from backend.schemas.decision import AIDecisionResult
from backend.schemas.recovery import EligibilityResult
from backend.schemas.risk import RiskResult
from backend.services.preprocessing import preprocess_transaction
from backend.services.recovery_agent import RecoveryAgent
from backend.llm.prompts import SYSTEM_RECOVERY_PROMPT, build_user_prompt
from backend.llm.inference import get_local_llm


class LLMDecisionAdapter:
    """
    Adapter interface for RecoverAI LLM Decision Agents.
    Supports LLM_PROVIDER=simulation and LLM_PROVIDER=huggingface (local PyTorch/Transformers LLM).
    """

    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or os.environ.get("LLM_PROVIDER", "simulation")).lower()
        self.fallback_agent = RecoveryAgent()

    def generate_decision(
        self,
        transaction: Union[TransactionInput, Dict[str, Any]],
        eligibility: Optional[EligibilityResult] = None,
        risk: Optional[RiskResult] = None
    ) -> AIDecisionResult:
        if not isinstance(transaction, TransactionInput):
            transaction = preprocess_transaction(transaction)

        tx_dict = transaction.model_dump() if hasattr(transaction, "model_dump") else (transaction.dict() if hasattr(transaction, "dict") else dict(transaction))
        el_dict = eligibility.model_dump() if eligibility and hasattr(eligibility, "model_dump") else (eligibility.dict() if eligibility and hasattr(eligibility, "dict") else {"eligible": True, "reason": "Eligible"})
        rk_dict = risk.model_dump() if risk and hasattr(risk, "model_dump") else (risk.dict() if risk and hasattr(risk, "dict") else {"risk_score": 40, "risk_level": "medium"})

        user_prompt = build_user_prompt(tx_dict, el_dict, rk_dict)

        # 1. Real Local Hugging Face Model Inference
        if self.provider == "huggingface":
            try:
                local_llm = get_local_llm()
                res = local_llm.generate(SYSTEM_RECOVERY_PROMPT, user_prompt)
                return AIDecisionResult(
                    action=res["action"],
                    diagnosis=res["diagnosis"],
                    reason=res["reason"],
                    confidence=res["confidence"]
                )
            except Exception as err:
                print(f"[LLM Adapter Error] Real LLM inference failed: {err}")
                return AIDecisionResult(
                    action="stop",
                    diagnosis="Local LLM Inference Error",
                    reason=f"Failed to generate decision via Hugging Face model: {str(err)}",
                    confidence=0.50
                )

        # 2. Simulation Mode Fallback
        fallback_res = self.fallback_agent.analyze(transaction, eligibility=eligibility, risk=risk)
        return AIDecisionResult(
            action=fallback_res.action,
            diagnosis=f"[LLM-SIMULATED] {fallback_res.diagnosis}",
            reason=f"LLM Decision Agent evaluated prompt signals: {fallback_res.reason}",
            confidence=min(0.95, round(fallback_res.confidence + 0.02, 2))
        )


def decide_recovery_llm(
    transaction: Union[TransactionInput, Dict[str, Any]],
    eligibility: Optional[EligibilityResult] = None,
    risk: Optional[RiskResult] = None
) -> AIDecisionResult:
    adapter = LLMDecisionAdapter()
    return adapter.generate_decision(transaction, eligibility, risk)
