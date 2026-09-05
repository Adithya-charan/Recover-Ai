import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.schemas.transaction import TransactionInput
from backend.services.risk_detector import RiskDetector, calculate_risk


class TestRiskDetector(unittest.TestCase):

    def setUp(self):
        self.detector = RiskDetector()

    def test_success_transaction_low_risk(self):
        tx = TransactionInput(
            transaction_id="TX01",
            customer_id="C01",
            amount=1000,
            payment_status="success"
        )
        res = self.detector.evaluate(tx)
        self.assertEqual(res.risk_level, "low")
        self.assertEqual(res.detected_revenue_at_risk, 0.0)

    def test_timeout_failed_transaction(self):
        tx = TransactionInput(
            transaction_id="TX02",
            customer_id="C02",
            amount=2500,
            payment_status="failed",
            failure_reason="timeout",
            customer_previous_payments=6,
            customer_previous_failures=1
        )
        res = self.detector.evaluate(tx)
        self.assertGreaterEqual(res.risk_score, 70)
        self.assertEqual(res.risk_level, "high")
        self.assertEqual(res.detected_revenue_at_risk, 2500.0)

    def test_bank_decline_transaction(self):
        tx = TransactionInput(
            transaction_id="TX03",
            customer_id="C03",
            amount=1500,
            payment_status="failed",
            failure_reason="bank_declined",
            attempt_count=1
        )
        res = self.detector.evaluate(tx)
        self.assertIn(res.risk_level, ["medium", "high"])

    def test_score_boundaries(self):
        tx = TransactionInput(
            transaction_id="TX04",
            customer_id="C04",
            amount=0,
            payment_status="success",
            attempt_count=5,
            days_since_event=30
        )
        res = self.detector.evaluate(tx)
        self.assertGreaterEqual(res.risk_score, 0)
        self.assertLessEqual(res.risk_score, 100)
        self.assertGreaterEqual(res.confidence, 0.0)
        self.assertLessEqual(res.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()
