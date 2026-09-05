import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.schemas.transaction import TransactionInput
from backend.schemas.risk import RiskResult
from backend.schemas.decision import AIDecisionResult
from backend.schemas.policy import PolicyResult
from backend.schemas.execution import ExecutionResult
from backend.schemas.recovery import EligibilityResult, PipelineResult


class TestSchemas(unittest.TestCase):

    def test_transaction_input_defaults_and_coercion(self):
        data = {
            "transaction_id": "TX00001",
            "customer_id": "CUST1001",
            "amount": "1999.50",
            "payment_status": "FAILED",
            "failure_reason": "TIMEOUT",
            "attempt_count": "2",
            "customer_previous_payments": "5",
            "customer_previous_failures": "1",
            "days_since_event": "3",
            "subscription_status": "ACTIVE"
        }
        tx = TransactionInput(**data)
        self.assertEqual(tx.transaction_id, "TX00001")
        self.assertEqual(tx.customer_id, "CUST1001")
        self.assertEqual(tx.amount, 1999.50)
        self.assertEqual(tx.payment_status, "failed")
        self.assertEqual(tx.failure_reason, "timeout")
        self.assertEqual(tx.attempt_count, 2)
        self.assertEqual(tx.customer_previous_payments, 5)
        self.assertEqual(tx.customer_previous_failures, 1)
        self.assertEqual(tx.days_since_event, 3)
        self.assertEqual(tx.subscription_status, "active")

    def test_transaction_input_malformed_values(self):
        data = {
            "transaction_id": "",
            "customer_id": None,
            "amount": "invalid_num",
            "payment_status": "UNKNOWN_STATUS",
            "failure_reason": None,
            "attempt_count": -5,
            "customer_previous_payments": None,
            "days_since_event": "abc"
        }
        tx = TransactionInput(**data)
        self.assertEqual(tx.transaction_id, "UNKNOWN")
        self.assertEqual(tx.customer_id, "UNKNOWN")
        self.assertEqual(tx.amount, 0.0)
        self.assertEqual(tx.payment_status, "failed")
        self.assertEqual(tx.failure_reason, "unknown")
        self.assertEqual(tx.attempt_count, 0)
        self.assertEqual(tx.customer_previous_payments, 0)
        self.assertEqual(tx.days_since_event, 0)

    def test_sub_schemas(self):
        eligibility = EligibilityResult(eligible=True, reason="Criteria met")
        self.assertTrue(eligibility.eligible)

        risk = RiskResult(risk_score=40, risk_level="medium", confidence=0.9, model_version="risk-v1", detected_revenue_at_risk=1999.0)
        self.assertEqual(risk.risk_score, 40)
        self.assertEqual(risk.risk_level, "medium")

        decision = AIDecisionResult(action="retry", diagnosis="Temporary timeout", reason="Customer history solid", confidence=0.95)
        self.assertEqual(decision.action, "retry")

        policy = PolicyResult(allowed=False, policy_status="blocked", reason="Max retries reached")
        self.assertFalse(policy.allowed)
        self.assertEqual(policy.policy_status, "blocked")

        execution = ExecutionResult(execution_status="BLOCKED", recovery_status="not_attempted", recovered_amount=0.0, execution_message="Blocked by policy")
        self.assertEqual(execution.execution_status, "BLOCKED")


if __name__ == "__main__":
    unittest.main()
