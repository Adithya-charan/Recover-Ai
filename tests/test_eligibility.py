import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.schemas.transaction import TransactionInput
from backend.services.eligibility_engine import EligibilityEngine, check_eligibility


class TestEligibility(unittest.TestCase):

    def setUp(self):
        self.engine = EligibilityEngine()

    def test_successful_transaction(self):
        tx = TransactionInput(
            transaction_id="TX001",
            customer_id="CUST01",
            amount=1000,
            payment_status="success",
            failure_reason=""
        )
        res = self.engine.evaluate(tx)
        self.assertFalse(res.eligible)
        self.assertIn("already successful", res.reason)

    def test_failed_eligible_timeout(self):
        tx = TransactionInput(
            transaction_id="TX002",
            customer_id="CUST02",
            amount=2000,
            payment_status="failed",
            failure_reason="timeout",
            attempt_count=1
        )
        res = self.engine.evaluate(tx)
        self.assertTrue(res.eligible)
        self.assertIn("timeout", res.reason)

    def test_bank_declined_eligible_with_history(self):
        tx = TransactionInput(
            transaction_id="TX003",
            customer_id="CUST03",
            amount=3000,
            payment_status="failed",
            failure_reason="bank_declined",
            attempt_count=1,
            customer_previous_payments=5,
            customer_previous_failures=1
        )
        res = self.engine.evaluate(tx)
        self.assertTrue(res.eligible)
        self.assertIn("bank decline", res.reason)

    def test_bank_declined_ineligible_without_history(self):
        tx = TransactionInput(
            transaction_id="TX004",
            customer_id="CUST04",
            amount=3000,
            payment_status="failed",
            failure_reason="bank_declined",
            attempt_count=3,
            customer_previous_payments=0,
            customer_previous_failures=5
        )
        res = self.engine.evaluate(tx)
        self.assertFalse(res.eligible)

    def test_insufficient_funds_ineligible(self):
        tx = TransactionInput(
            transaction_id="TX005",
            customer_id="CUST05",
            amount=1500,
            payment_status="failed",
            failure_reason="insufficient_funds"
        )
        res = self.engine.evaluate(tx)
        self.assertFalse(res.eligible)
        self.assertIn("Insufficient funds", res.reason)

    def test_abandoned_transaction_eligible(self):
        tx = TransactionInput(
            transaction_id="TX006",
            customer_id="CUST06",
            amount=500,
            payment_status="abandoned",
            days_since_event=3
        )
        res = self.engine.evaluate(tx)
        self.assertTrue(res.eligible)
        self.assertIn("abandonment", res.reason)

    def test_abandoned_transaction_stale(self):
        tx = TransactionInput(
            transaction_id="TX007",
            customer_id="CUST07",
            amount=500,
            payment_status="abandoned",
            days_since_event=40
        )
        res = self.engine.evaluate(tx)
        self.assertFalse(res.eligible)


if __name__ == "__main__":
    unittest.main()
