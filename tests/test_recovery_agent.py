import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.schemas.transaction import TransactionInput
from backend.services.recovery_agent import RecoveryAgent, recommend_action


class TestRecoveryAgent(unittest.TestCase):

    def setUp(self):
        self.agent = RecoveryAgent()

    def test_successful_payment(self):
        tx = TransactionInput(
            transaction_id="TX01",
            customer_id="C01",
            amount=1000,
            payment_status="success"
        )
        res = self.agent.analyze(tx)
        self.assertEqual(res.action, "stop")
        self.assertEqual(res.diagnosis, "Payment already successful")

    def test_recent_abandoned_checkout(self):
        tx = TransactionInput(
            transaction_id="TX02",
            customer_id="C02",
            amount=500,
            payment_status="abandoned",
            days_since_event=2
        )
        res = self.agent.analyze(tx)
        self.assertEqual(res.action, "reminder")

    def test_temporary_timeout_retry(self):
        tx = TransactionInput(
            transaction_id="TX03",
            customer_id="C03",
            amount=1999,
            payment_status="failed",
            failure_reason="timeout",
            attempt_count=1,
            days_since_event=2
        )
        res = self.agent.analyze(tx)
        self.assertEqual(res.action, "retry")
        self.assertGreaterEqual(res.confidence, 0.70)

    def test_bank_decline_with_good_history(self):
        tx = TransactionInput(
            transaction_id="TX04",
            customer_id="C04",
            amount=1999,
            payment_status="failed",
            failure_reason="bank_declined",
            attempt_count=1,
            customer_previous_payments=4,
            customer_previous_failures=1
        )
        res = self.agent.analyze(tx)
        self.assertEqual(res.action, "retry")

    def test_insufficient_funds_escalate(self):
        tx = TransactionInput(
            transaction_id="TX05",
            customer_id="C05",
            amount=1999,
            payment_status="failed",
            failure_reason="insufficient_funds"
        )
        res = self.agent.analyze(tx)
        self.assertEqual(res.action, "escalate")


if __name__ == "__main__":
    unittest.main()
