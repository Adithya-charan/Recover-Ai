import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.schemas.transaction import TransactionInput
from backend.schemas.decision import AIDecisionResult
from backend.schemas.policy import PolicyResult
from backend.llm.prompts import SYSTEM_RECOVERY_PROMPT, build_user_prompt
from backend.llm.model_adapter import LLMDecisionAdapter, decide_recovery_llm
from backend.services.policy_engine import PolicyEngine


class TestLLM(unittest.TestCase):

    def setUp(self):
        self.sim_adapter = LLMDecisionAdapter(provider="simulation")
        self.hf_adapter = LLMDecisionAdapter(provider="huggingface")

    def test_prompts_content(self):
        self.assertIn("The Policy Engine is the final authority", SYSTEM_RECOVERY_PROMPT)
        self.assertIn("retry", SYSTEM_RECOVERY_PROMPT)
        
        tx_data = {"transaction_id": "TX_TEST", "amount": 1999}
        user_p = build_user_prompt(tx_data, {"eligible": True}, {"risk_score": 30})
        self.assertIn("INR 1999", user_p)
        self.assertIn("TX_TEST", user_p)

    def test_llm_simulation_mode(self):
        tx = TransactionInput(
            transaction_id="TX_LLM_01",
            customer_id="C01",
            amount=1999,
            payment_status="failed",
            failure_reason="timeout",
            attempt_count=1
        )
        res = self.sim_adapter.generate_decision(tx)
        self.assertIsInstance(res, AIDecisionResult)
        self.assertEqual(res.action, "retry")
        self.assertIn("LLM-SIMULATED", res.diagnosis)

    def test_policy_engine_overrides_llm(self):
        tx = TransactionInput(
            transaction_id="TX_LLM_02",
            customer_id="C02",
            amount=50000,
            payment_status="failed",
            failure_reason="timeout",
            attempt_count=1
        )
        llm_dec = AIDecisionResult(
            action="retry",
            diagnosis="Temporary failure",
            reason="LLM suggests retrying",
            confidence=0.92
        )
        engine = PolicyEngine()
        pol_res = engine.evaluate(tx, decision=llm_dec)
        self.assertFalse(pol_res.allowed)
        self.assertEqual(pol_res.policy_status, "blocked")
        self.assertIn("exceeds", pol_res.reason)


if __name__ == "__main__":
    unittest.main()
