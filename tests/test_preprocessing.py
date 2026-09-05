import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.schemas.transaction import TransactionInput
from backend.services.preprocessing import preprocess_transaction


class TestPreprocessing(unittest.TestCase):

    def test_normal_valid_transaction(self):
        raw = {
            "transaction_id": "TX00001",
            "customer_id": "CUST1001",
            "amount": 1999.0,
            "payment_status": "failed",
            "failure_reason": "timeout",
            "attempt_count": 2,
            "customer_previous_payments": 5,
            "customer_previous_failures": 1,
            "days_since_event": 3,
            "subscription_status": "active"
        }
        res = preprocess_transaction(raw)
        self.assertIsInstance(res, TransactionInput)
        self.assertEqual(res.transaction_id, "TX00001")
        self.assertEqual(res.amount, 1999.0)
        self.assertEqual(res.payment_status, "failed")

    def test_string_numeric_values(self):
        raw = {
            "transaction_id": "TX00002",
            "customer_id": "CUST1002",
            "amount": "1999",
            "attempt_count": "2",
            "days_since_event": "5"
        }
        res = preprocess_transaction(raw)
        self.assertEqual(res.amount, 1999.0)
        self.assertEqual(res.attempt_count, 2)
        self.assertEqual(res.days_since_event, 5)

    def test_missing_none_fields(self):
        raw = {
            "transaction_id": "TX00003",
            "customer_id": None,
            "amount": None,
            "payment_status": None,
            "failure_reason": None
        }
        res = preprocess_transaction(raw)
        self.assertEqual(res.customer_id, "UNKNOWN")
        self.assertEqual(res.amount, 0.0)
        self.assertEqual(res.payment_status, "failed")
        self.assertEqual(res.failure_reason, "unknown")

    def test_empty_strings(self):
        raw = {
            "transaction_id": "",
            "customer_id": "   ",
            "amount": "",
            "attempt_count": ""
        }
        res = preprocess_transaction(raw)
        self.assertEqual(res.transaction_id, "UNKNOWN")
        self.assertEqual(res.customer_id, "UNKNOWN")
        self.assertEqual(res.amount, 0.0)
        self.assertEqual(res.attempt_count, 1)

    def test_invalid_values(self):
        raw = {
            "transaction_id": "TX00004",
            "customer_id": "CUST1004",
            "amount": -500.0,
            "attempt_count": -2,
            "payment_status": "INVALID_STATUS"
        }
        res = preprocess_transaction(raw)
        self.assertEqual(res.amount, 0.0)
        self.assertEqual(res.attempt_count, 0)
        self.assertEqual(res.payment_status, "failed")

    def test_no_input_mutation(self):
        raw = {
            "transaction_id": "TX00005",
            "amount": "1500",
            "payment_status": "FAILED"
        }
        original = raw.copy()
        _ = preprocess_transaction(raw)
        self.assertEqual(raw, original)


if __name__ == "__main__":
    unittest.main()
