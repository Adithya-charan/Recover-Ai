import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.schemas.transaction import TransactionInput
from backend.schemas.decision import AIDecisionResult
from backend.schemas.policy import PolicyResult
from backend.services.recovery_executor import RecoveryExecutor, execute_action


class TestRecoveryExecutor(unittest.TestCase):

    def setUp(self):
        self.executor = RecoveryExecutor()

    def test_blocked_policy_never_executes(self):
        tx = TransactionInput(
            transaction_id="TX01",
            customer_id="C01",
            amount=1000
        )
        pol = PolicyResult(allowed=False, policy_status="blocked", reason="Max retries")
        res = self.executor.execute(tx, policy=pol)
        self.assertEqual(res.execution_status, "BLOCKED")
        self.assertEqual(res.recovery_status, "not_attempted")
        self.assertEqual(res.recovered_amount, 0.0)

    def test_allowed_retry_simulation(self):
        tx = TransactionInput(
            transaction_id="TX02",
            customer_id="C02",
            amount=1999
        )
        dec = AIDecisionResult(action="retry", diagnosis="Timeout", reason="Retry", confidence=0.9)
        pol = PolicyResult(allowed=True, policy_status="allowed", reason="Passed policy")
        res = self.executor.execute(tx, decision=dec, policy=pol)
        self.assertIn(res.execution_status, ["SIMULATED", "EXECUTED"])
        self.assertIn(res.recovery_status, ["RECOVERED", "FAILED"])

    def test_allowed_reminder_simulation(self):
        tx = TransactionInput(
            transaction_id="TX03",
            customer_id="C03",
            amount=500
        )
        dec = AIDecisionResult(action="reminder", diagnosis="Abandoned", reason="Reminder", confidence=0.88)
        pol = PolicyResult(allowed=True, policy_status="allowed", reason="Passed policy")
        res = self.executor.execute(tx, decision=dec, policy=pol)
        self.assertEqual(res.recovery_status, "FOLLOW_UP")
        self.assertEqual(res.recovered_amount, 0.0)


if __name__ == "__main__":
    unittest.main()
