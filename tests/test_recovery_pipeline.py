import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.schemas.transaction import TransactionInput
from backend.services.recovery_pipeline import process_transaction, RecoveryPipeline


class TestRecoveryPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = RecoveryPipeline()

    def test_scenario_1_successful_payment(self):
        raw = {"transaction_id": "TX_SUCCESS", "customer_id": "C01", "amount": 1000, "payment_status": "success"}
        res = self.pipeline.process_transaction(raw)
        self.assertFalse(res.eligibility.eligible)
        self.assertEqual(res.decision.action, "stop")
        self.assertFalse(res.policy.allowed)
        self.assertEqual(res.execution.execution_status, "BLOCKED")
        self.assertEqual(res.final_status, "stopped")

    def test_scenario_2_recoverable_timeout(self):
        raw = {
            "transaction_id": "TX_TIMEOUT",
            "customer_id": "C02",
            "amount": 1999,
            "payment_status": "failed",
            "failure_reason": "timeout",
            "attempt_count": 1,
            "days_since_event": 2
        }
        res = self.pipeline.process_transaction(raw)
        self.assertTrue(res.eligibility.eligible)
        self.assertEqual(res.decision.action, "retry")
        self.assertTrue(res.policy.allowed)
        self.assertIn(res.final_status, ["recovered", "failed"])

    def test_scenario_3_bank_decline_good_history(self):
        raw = {
            "transaction_id": "TX_BANK",
            "customer_id": "C03",
            "amount": 1999,
            "payment_status": "failed",
            "failure_reason": "bank_declined",
            "attempt_count": 1,
            "customer_previous_payments": 5,
            "customer_previous_failures": 1,
            "days_since_event": 2
        }
        res = self.pipeline.process_transaction(raw)
        self.assertTrue(res.eligibility.eligible)
        self.assertEqual(res.decision.action, "retry")
        self.assertTrue(res.policy.allowed)

    def test_scenario_4_insufficient_funds(self):
        raw = {
            "transaction_id": "TX_FUNDS",
            "customer_id": "C04",
            "amount": 1999,
            "payment_status": "failed",
            "failure_reason": "insufficient_funds"
        }
        res = self.pipeline.process_transaction(raw)
        self.assertFalse(res.eligibility.eligible)
        self.assertEqual(res.decision.action, "escalate")
        self.assertFalse(res.policy.allowed)
        self.assertEqual(res.execution.execution_status, "BLOCKED")

    def test_scenario_5_maximum_retries(self):
        raw = {
            "transaction_id": "TX_MAX_RETRY",
            "customer_id": "C05",
            "amount": 1999,
            "payment_status": "failed",
            "failure_reason": "timeout",
            "attempt_count": 4
        }
        res = self.pipeline.process_transaction(raw)
        self.assertFalse(res.eligibility.eligible)
        self.assertFalse(res.policy.allowed)

    def test_scenario_6_excessive_amount_policy_block(self):
        raw = {
            "transaction_id": "TX_HIGH_AMT",
            "customer_id": "C06",
            "amount": 50000,
            "payment_status": "failed",
            "failure_reason": "timeout",
            "attempt_count": 1,
            "days_since_event": 2
        }
        res = self.pipeline.process_transaction(raw)
        self.assertTrue(res.eligibility.eligible)
        self.assertEqual(res.decision.action, "retry")
        self.assertFalse(res.policy.allowed)
        self.assertEqual(res.execution.execution_status, "BLOCKED")
        self.assertEqual(res.final_status, "blocked")

    def test_scenario_7_abandoned_checkout(self):
        raw = {
            "transaction_id": "TX_ABANDONED",
            "customer_id": "C07",
            "amount": 499,
            "payment_status": "abandoned",
            "days_since_event": 3
        }
        res = self.pipeline.process_transaction(raw)
        self.assertTrue(res.eligibility.eligible)
        self.assertEqual(res.decision.action, "reminder")
        self.assertTrue(res.policy.allowed)
        self.assertEqual(res.final_status, "follow_up")

    def test_scenario_8_dirty_invalid_input(self):
        raw = {"transaction_id": None, "amount": "invalid", "payment_status": None}
        res = self.pipeline.process_transaction(raw)
        self.assertIsNotNone(res.transaction_id)
        self.assertIsNotNone(res.final_status)


if __name__ == "__main__":
    unittest.main()
