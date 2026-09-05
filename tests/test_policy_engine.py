import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.schemas.transaction import TransactionInput
from backend.schemas.decision import AIDecisionResult
from backend.schemas.recovery import EligibilityResult
from backend.services.policy_engine import PolicyEngine, CasePolicyEngine, evaluate_policy


class TestPolicyEngine(unittest.TestCase):

    def setUp(self):
        self.engine = PolicyEngine()

    def test_allowed_retry(self):
        tx = TransactionInput(
            transaction_id="TX01", customer_id="C01", amount=1999,
            payment_status="failed", failure_reason="timeout",
            attempt_count=1, days_since_event=2)
        dec = AIDecisionResult(action="retry", diagnosis="Timeout", reason="Retry", confidence=0.9)
        el = EligibilityResult(eligible=True, reason="Eligible")
        res = self.engine.evaluate(tx, decision=dec, eligibility=el)
        self.assertTrue(res.allowed)
        self.assertEqual(res.policy_status, "allowed")

    def test_blocked_max_retries(self):
        tx = TransactionInput(
            transaction_id="TX02", customer_id="C02", amount=1999,
            payment_status="failed", failure_reason="timeout",
            attempt_count=3, days_since_event=2)
        dec = AIDecisionResult(action="retry", diagnosis="Timeout", reason="Retry", confidence=0.9)
        el = EligibilityResult(eligible=True, reason="Eligible")
        res = self.engine.evaluate(tx, decision=dec, eligibility=el)
        self.assertFalse(res.allowed)
        self.assertIn("Maximum retry attempts reached", res.reason)

    def test_blocked_excessive_amount(self):
        tx = TransactionInput(
            transaction_id="TX03", customer_id="C03", amount=50000,
            payment_status="failed", failure_reason="timeout",
            attempt_count=1, days_since_event=2)
        dec = AIDecisionResult(action="retry", diagnosis="Timeout", reason="Retry", confidence=0.9)
        el = EligibilityResult(eligible=True, reason="Eligible")
        res = self.engine.evaluate(tx, decision=dec, eligibility=el)
        self.assertFalse(res.allowed)
        self.assertIn("exceeds", res.reason)

    def test_blocked_unsupported_action(self):
        tx = TransactionInput(
            transaction_id="TX04", customer_id="C04", amount=1000,
            payment_status="failed", failure_reason="insufficient_funds")
        dec = AIDecisionResult(action="escalate", diagnosis="Insufficient funds",
                               reason="Escalate", confidence=0.9)
        el = EligibilityResult(eligible=False, reason="Ineligible")
        res = self.engine.evaluate(tx, decision=dec, eligibility=el)
        self.assertFalse(res.allowed)


class TestCasePolicyEngine(unittest.TestCase):

    def setUp(self):
        self.engine = CasePolicyEngine()

    def _ok(self, **kw):
        defaults = dict(
            case_type="PAYMENT_FAILURE", action="retry",
            is_eligible=True, eligibility_reason="ok",
            amount=999.0, attempt_count=1, max_attempts=3,
            days_since_event=2, days_overdue=0,
            risk_score=40, failure_reason="timeout",
        )
        defaults.update(kw)
        return self.engine.evaluate(**defaults)

    # --- action whitelist ---

    def test_payment_failure_retry_allowed(self):
        res = self._ok(case_type="PAYMENT_FAILURE", action="retry")
        self.assertTrue(res.allowed)

    def test_payment_failure_voice_call_blocked(self):
        res = self._ok(case_type="PAYMENT_FAILURE", action="voice_call")
        self.assertFalse(res.allowed)
        self.assertIn("voice_call", res.reason)

    def test_checkout_abandonment_reminder_allowed(self):
        res = self._ok(case_type="CHECKOUT_ABANDONMENT", action="reminder")
        self.assertTrue(res.allowed)

    def test_checkout_abandonment_retry_blocked(self):
        res = self._ok(case_type="CHECKOUT_ABANDONMENT", action="retry")
        self.assertFalse(res.allowed)

    def test_b2b_voice_call_allowed(self):
        res = self._ok(case_type="B2B_RECEIVABLE", action="voice_call")
        self.assertTrue(res.allowed)

    def test_b2b_retry_blocked_by_whitelist(self):
        res = self._ok(case_type="B2B_RECEIVABLE", action="retry")
        self.assertFalse(res.allowed)

    def test_mandate_schedule_mandate_allowed(self):
        res = self._ok(case_type="MANDATE_FAILURE", action="schedule_mandate")
        self.assertTrue(res.allowed)

    def test_promise_to_pay_collect_allowed(self):
        res = self._ok(case_type="PROMISE_TO_PAY", action="collect_promise")
        self.assertTrue(res.allowed)

    # --- eligibility gate ---

    def test_ineligible_case_blocked(self):
        res = self._ok(is_eligible=False, eligibility_reason="Subscription canceled")
        self.assertFalse(res.allowed)
        self.assertIn("ineligible", res.reason.lower())

    # --- attempt limits ---

    def test_retry_limit_enforced(self):
        res = self._ok(case_type="PAYMENT_FAILURE", action="retry",
                       attempt_count=5, max_attempts=2)
        self.assertFalse(res.allowed)
        self.assertIn("Attempt limit", res.reason)

    def test_mandate_presentment_limit(self):
        res = self._ok(case_type="MANDATE_FAILURE", action="schedule_mandate",
                       attempt_count=4, max_attempts=3)
        self.assertFalse(res.allowed)

    # --- recovery window ---

    def test_payment_failure_outside_window(self):
        res = self._ok(case_type="PAYMENT_FAILURE", action="retry", days_since_event=10)
        self.assertFalse(res.allowed)
        self.assertIn("window", res.reason)

    def test_b2b_60_day_window(self):
        res = self._ok(case_type="B2B_RECEIVABLE", action="reminder", days_since_event=55)
        self.assertTrue(res.allowed)

    def test_b2b_outside_60_day_window(self):
        res = self._ok(case_type="B2B_RECEIVABLE", action="reminder", days_since_event=65)
        self.assertFalse(res.allowed)

    def test_promise_to_pay_no_window(self):
        # PROMISE_TO_PAY has no recovery window limit
        res = self._ok(case_type="PROMISE_TO_PAY", action="collect_promise", days_since_event=200)
        self.assertTrue(res.allowed)

    # --- high-risk escalation ---

    def test_high_risk_escalated(self):
        res = self._ok(risk_score=90)
        self.assertFalse(res.allowed)
        self.assertEqual(res.policy_status, "escalated")

    # --- B2B mandatory escalation ---

    def test_b2b_overdue_30_days_must_escalate(self):
        res = self._ok(case_type="B2B_RECEIVABLE", action="reminder", days_overdue=35)
        self.assertFalse(res.allowed)
        self.assertEqual(res.policy_status, "escalated")

    def test_b2b_overdue_30_days_escalate_action_allowed(self):
        res = self._ok(case_type="B2B_RECEIVABLE", action="escalate", days_overdue=35)
        self.assertTrue(res.allowed)

    # --- mandate irrecoverable codes ---

    def test_mandate_revoked_blocked(self):
        res = self._ok(case_type="MANDATE_FAILURE", action="schedule_mandate",
                       failure_reason="mandate_revoked")
        self.assertFalse(res.allowed)

    def test_mandate_account_closed_blocked(self):
        res = self._ok(case_type="MANDATE_FAILURE", action="schedule_mandate",
                       failure_reason="account_closed")
        self.assertFalse(res.allowed)

    # --- promise-to-pay grace period ---

    def test_promise_broken_beyond_grace_escalated(self):
        res = self._ok(case_type="PROMISE_TO_PAY", action="collect_promise",
                       failure_reason="promise_broken", days_overdue=5)
        self.assertFalse(res.allowed)
        self.assertEqual(res.policy_status, "escalated")

    def test_promise_broken_within_grace_allowed(self):
        res = self._ok(case_type="PROMISE_TO_PAY", action="collect_promise",
                       failure_reason="promise_broken", days_overdue=1)
        self.assertTrue(res.allowed)


if __name__ == "__main__":
    unittest.main()
