import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.payment.sandbox import SandboxPaymentAdapter
from backend.payment.provider import execute_payment_recovery


class TestPayment(unittest.TestCase):

    def setUp(self):
        self.sandbox = SandboxPaymentAdapter()

    def test_create_order(self):
        order = self.sandbox.create_payment("TX_PAY_01", 1999.0, "CUST01")
        self.assertEqual(order["transaction_id"], "TX_PAY_01")
        self.assertEqual(order["status"], "created")

    def test_retry_payment_sandbox(self):
        res = execute_payment_recovery("TX_PAY_02", 2500.0, "CUST02")
        self.assertIn("status", res)
        self.assertIn("recovered", res)
        self.assertEqual(res["amount"], 2500.0)

    def test_webhook_processing(self):
        payload = {"event": "payment.captured", "payload": {"payment": {"entity": {"notes": {"transaction_id": "TX_PAY_03"}}}}}
        res = self.sandbox.handle_webhook(payload)
        self.assertTrue(res["verified"])
        self.assertEqual(res["transaction_id"], "TX_PAY_03")


if __name__ == "__main__":
    unittest.main()
