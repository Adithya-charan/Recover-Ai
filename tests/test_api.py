import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.main import app


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")

    def test_dashboard(self):
        res = self.client.get("/api/dashboard")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_transactions", data)

    def test_predict_recovery(self):
        payload = {
            "transaction_id": "TX_TEST_API",
            "customer_id": "CUST101",
            "amount": 1999,
            "payment_status": "failed",
            "failure_reason": "timeout",
            "attempt_count": 1,
            "days_since_event": 2
        }
        res = self.client.post("/api/recovery/predict", json=payload)
        self.assertEqual(res.status_code, 200)

    def test_ml_predict(self):
        payload = {
            "transaction_id": "TX_ML_API",
            "customer_id": "CUST102",
            "amount": 2500,
            "payment_status": "failed",
            "failure_reason": "timeout"
        }
        res = self.client.post("/api/ml/predict", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertIn("recovery_probability", res.json())

    def test_llm_decision(self):
        payload = {
            "transaction_id": "TX_LLM_API",
            "customer_id": "CUST103",
            "amount": 1500,
            "payment_status": "abandoned"
        }
        res = self.client.post("/api/llm/decision", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertIn("action", res.json())

    def test_recovery_execute(self):
        payload = {
            "transaction_id": "TX_EXEC_API",
            "customer_id": "CUST104",
            "amount": 1999,
            "payment_status": "failed",
            "failure_reason": "timeout",
            "attempt_count": 1
        }
        res = self.client.post("/api/recovery/execute", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("ml_insights", data)
        self.assertIn("communications", data)


if __name__ == "__main__":
    unittest.main()
