import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.schemas.transaction import TransactionInput
from backend.services.recovery_orchestrator import UnifiedRecoveryOrchestrator, process_orchestrated_recovery


class TestRecoveryOrchestrator(unittest.TestCase):

    def setUp(self):
        self.orchestrator = UnifiedRecoveryOrchestrator()

    def test_full_orchestrated_recovery_retry(self):
        tx = TransactionInput(
            transaction_id="TX_ORCH_01",
            customer_id="C01",
            amount=1999,
            payment_status="failed",
            failure_reason="timeout",
            attempt_count=1,
            days_since_event=2
        )
        res = self.orchestrator.process_recovery(tx)
        self.assertIn("pipeline_result", res)
        self.assertIn("ml_insights", res)
        self.assertIn("llm_decision", res)
        self.assertIn("payment_result", res)
        self.assertIn("communications", res)
        self.assertTrue(len(res["communications"]) > 0)

    def test_orchestrated_blocked_policy(self):
        tx = TransactionInput(
            transaction_id="TX_ORCH_02",
            customer_id="C02",
            amount=50000,
            payment_status="failed",
            failure_reason="timeout",
            attempt_count=1
        )
        res = self.orchestrator.process_recovery(tx)
        self.assertEqual(res["pipeline_result"].policy.policy_status, "blocked")
        self.assertEqual(len(res["communications"]), 0)


if __name__ == "__main__":
    unittest.main()
