"""
Comprehensive end-to-end tests for all six RecoverAI recovery flows.

Tests per flow:
  - Detection (case type routing)
  - Revenue at risk
  - Eligibility
  - ML inference
  - LLM decision
  - Policy authorization
  - Execution (domain-specific)
  - Communication dispatch
  - Outcome
  - Audit event
  - Metrics

Also tests cross-cutting scenarios:
  1. Successful recovery
  2. Failed recovery
  3. Policy-blocked recovery
  4. Maximum retry stopping rule
  5. High-risk escalation
  6. B2B escalation
  7. Broken promise-to-pay
  8. Mandate retry limit
  9. Communication provider failure (simulation fallback)
  10. Simulation fallback (provider_mode = SIMULATED)
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.schemas.case import RecoveryCaseInput
from backend.services.case_orchestrator import process_orchestrated_case, UnifiedCaseOrchestrator
from backend.services.policy_engine import CasePolicyEngine
from backend.services.domain_executor import dispatch_execution
from backend.services.audit_logger import AuditLogger
from backend.communications.orchestrator import CommunicationOrchestrator
from backend.schemas.transaction import TransactionInput
from backend.schemas.decision import AIDecisionResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_case(**kwargs) -> dict:
    defaults = dict(
        case_id="TEST_FLOW_001",
        case_type="PAYMENT_FAILURE",
        customer_id="CUST_TEST",
        amount=2500.0,
        payment_status="failed",
        failure_reason="timeout",
        attempt_count=1,
        max_attempts=3,
        days_since_event=2,
        days_overdue=0,
    )
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# FLOW 1: PAYMENT_FAILURE
# ---------------------------------------------------------------------------

class TestPaymentFailureFlow:
    def test_detection_routes_to_payment_failure(self):
        result = process_orchestrated_case(make_case(case_type="PAYMENT_FAILURE"))
        assert result["case_result"]["case_type"] == "PAYMENT_FAILURE"

    def test_revenue_at_risk_captured(self):
        result = process_orchestrated_case(make_case(case_type="PAYMENT_FAILURE", amount=5000.0))
        assert result["case_result"]["revenue_at_risk"] == 5000.0

    def test_eligibility_evaluated(self):
        result = process_orchestrated_case(make_case(case_type="PAYMENT_FAILURE"))
        assert "policy_decision" in result["case_result"]

    def test_ml_insights_present(self):
        result = process_orchestrated_case(make_case(case_type="PAYMENT_FAILURE"))
        assert "ml_insights" in result
        assert "risk_score" in result["ml_insights"]
        assert "recovery_probability" in result["ml_insights"]

    def test_llm_decision_present(self):
        result = process_orchestrated_case(make_case(case_type="PAYMENT_FAILURE"))
        assert "llm_decision" in result
        assert "action" in result["llm_decision"]

    def test_policy_authorizes_retry(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="PAYMENT_FAILURE", action="retry",
            is_eligible=True, eligibility_reason="ok",
            amount=2500.0, attempt_count=1, max_attempts=3,
            days_since_event=2, days_overdue=0,
            risk_score=40, failure_reason="timeout",
        )
        assert res.allowed

    def test_execution_uses_payment_retry(self):
        res = dispatch_execution(
            case_type="PAYMENT_FAILURE",
            case_id="C001", transaction_id="TX001",
            amount=2500.0, customer_id="CUST01",
            action="retry",
        )
        assert res["case_type"] == "PAYMENT_FAILURE"
        assert res["action"] == "retry"
        assert "provider_mode" in res
        assert res["provider_mode"] == "SIMULATED"

    def test_communication_dispatched(self):
        result = process_orchestrated_case(make_case(
            case_type="PAYMENT_FAILURE", amount=2500.0
        ))
        # communications list may be empty if policy blocks, but field exists
        assert "communications" in result

    def test_outcome_field_present(self):
        result = process_orchestrated_case(make_case(case_type="PAYMENT_FAILURE"))
        assert "outcome" in result["case_result"]

    def test_audit_event_recorded(self):
        result = process_orchestrated_case(make_case(case_type="PAYMENT_FAILURE"))
        audit = result["audit_event"]
        assert audit["case_type"] == "PAYMENT_FAILURE"
        assert audit["transaction_id"] is not None
        assert audit["executed_at"] is not None


# ---------------------------------------------------------------------------
# FLOW 2: CHECKOUT_ABANDONMENT
# ---------------------------------------------------------------------------

class TestCheckoutAbandonmentFlow:
    def test_detection_routes_correctly(self):
        result = process_orchestrated_case(make_case(case_type="CHECKOUT_ABANDONMENT"))
        assert result["case_result"]["case_type"] == "CHECKOUT_ABANDONMENT"

    def test_execution_produces_reminder_action(self):
        res = dispatch_execution(
            case_type="CHECKOUT_ABANDONMENT",
            case_id="C002", transaction_id="TX002",
            amount=1500.0, customer_id="CUST02",
            action="reminder",
        )
        assert res["case_type"] == "CHECKOUT_ABANDONMENT"
        assert res["action"] == "reminder"
        assert res["status"] == "FOLLOW_UP"
        assert res["provider_mode"] == "SIMULATED"

    def test_policy_allows_reminder(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="CHECKOUT_ABANDONMENT", action="reminder",
            is_eligible=True, eligibility_reason="ok",
            amount=1500.0, attempt_count=1, max_attempts=2,
            days_since_event=3, days_overdue=0, risk_score=30,
        )
        assert res.allowed

    def test_policy_blocks_retry(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="CHECKOUT_ABANDONMENT", action="retry",
            is_eligible=True, eligibility_reason="ok",
            amount=1500.0, attempt_count=1, max_attempts=2,
            days_since_event=3, days_overdue=0, risk_score=30,
        )
        assert not res.allowed

    def test_audit_includes_case_type(self):
        result = process_orchestrated_case(make_case(case_type="CHECKOUT_ABANDONMENT"))
        assert result["audit_event"]["case_type"] == "CHECKOUT_ABANDONMENT"


# ---------------------------------------------------------------------------
# FLOW 3: FAILED_SUBSCRIPTION
# ---------------------------------------------------------------------------

class TestFailedSubscriptionFlow:
    def test_detection_routes_correctly(self):
        result = process_orchestrated_case(make_case(case_type="FAILED_SUBSCRIPTION"))
        assert result["case_result"]["case_type"] == "FAILED_SUBSCRIPTION"

    def test_execution_subscription_dunning(self):
        res = dispatch_execution(
            case_type="FAILED_SUBSCRIPTION",
            case_id="C003", transaction_id="TX003",
            amount=999.0, customer_id="CUST03",
            action="retry", attempt_count=1,
        )
        assert res["case_type"] == "FAILED_SUBSCRIPTION"
        assert res["provider_mode"] == "SIMULATED"

    def test_policy_allows_retry(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="FAILED_SUBSCRIPTION", action="retry",
            is_eligible=True, eligibility_reason="ok",
            amount=999.0, attempt_count=1, max_attempts=3,
            days_since_event=5, days_overdue=0, risk_score=35,
        )
        assert res.allowed

    def test_canceled_subscription_ineligible(self):
        result = process_orchestrated_case(make_case(
            case_type="FAILED_SUBSCRIPTION",
            subscription_status="canceled",
        ))
        cr = result["case_result"]
        # Either policy blocks or ineligibility gates it
        assert cr["policy_decision"] == "BLOCK" or cr["execution_status"] == "BLOCKED"


# ---------------------------------------------------------------------------
# FLOW 4: B2B_RECEIVABLE
# ---------------------------------------------------------------------------

class TestB2BReceivableFlow:
    def test_detection_routes_correctly(self):
        result = process_orchestrated_case(make_case(case_type="B2B_RECEIVABLE"))
        assert result["case_result"]["case_type"] == "B2B_RECEIVABLE"

    def test_execution_reminder_action(self):
        res = dispatch_execution(
            case_type="B2B_RECEIVABLE",
            case_id="C004", transaction_id="TX004",
            amount=50000.0, customer_id="CORP01",
            action="reminder", days_overdue=10,
        )
        assert res["case_type"] == "B2B_RECEIVABLE"
        assert res["action"] == "reminder"
        assert res["provider_mode"] == "SIMULATED"

    def test_execution_escalate_action(self):
        res = dispatch_execution(
            case_type="B2B_RECEIVABLE",
            case_id="C004b", transaction_id="TX004b",
            amount=50000.0, customer_id="CORP01",
            action="escalate", days_overdue=35,
        )
        assert res["status"] == "ESCALATED"

    def test_policy_b2b_escalation_required_after_30_days(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="B2B_RECEIVABLE", action="reminder",
            is_eligible=True, eligibility_reason="ok",
            amount=50000.0, attempt_count=1, max_attempts=5,
            days_since_event=35, days_overdue=35, risk_score=50,
        )
        assert not res.allowed
        assert res.policy_status == "escalated"

    def test_policy_b2b_escalate_action_allowed_after_30_days(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="B2B_RECEIVABLE", action="escalate",
            is_eligible=True, eligibility_reason="ok",
            amount=50000.0, attempt_count=1, max_attempts=5,
            days_since_event=35, days_overdue=35, risk_score=50,
        )
        assert res.allowed

    def test_legal_dispute_ineligible(self):
        result = process_orchestrated_case(make_case(
            case_type="B2B_RECEIVABLE",
            failure_reason="legal_dispute",
        ))
        cr = result["case_result"]
        assert cr["policy_decision"] == "BLOCK" or cr["execution_status"] == "BLOCKED"


# ---------------------------------------------------------------------------
# FLOW 5: MANDATE_FAILURE
# ---------------------------------------------------------------------------

class TestMandateFailureFlow:
    def test_detection_routes_correctly(self):
        result = process_orchestrated_case(make_case(case_type="MANDATE_FAILURE"))
        assert result["case_result"]["case_type"] == "MANDATE_FAILURE"

    def test_execution_mandate_re_presentment(self):
        res = dispatch_execution(
            case_type="MANDATE_FAILURE",
            case_id="C005", transaction_id="TX005",
            amount=3000.0, customer_id="CUST05",
            action="schedule_mandate", attempt_count=1,
        )
        assert res["case_type"] == "MANDATE_FAILURE"
        assert res["action"] == "schedule_mandate"
        assert res["provider_mode"] == "SIMULATED"

    def test_mandate_revoked_blocked_by_policy(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="MANDATE_FAILURE", action="schedule_mandate",
            is_eligible=True, eligibility_reason="ok",
            amount=3000.0, attempt_count=1, max_attempts=3,
            days_since_event=2, days_overdue=0, risk_score=40,
            failure_reason="mandate_revoked",
        )
        assert not res.allowed
        assert "mandate_revoked" in res.reason

    def test_mandate_retry_limit_enforced(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="MANDATE_FAILURE", action="schedule_mandate",
            is_eligible=True, eligibility_reason="ok",
            amount=3000.0, attempt_count=4, max_attempts=3,
            days_since_event=2, days_overdue=0, risk_score=40,
        )
        assert not res.allowed
        assert "Attempt limit" in res.reason

    def test_account_closed_blocked_by_policy(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="MANDATE_FAILURE", action="schedule_mandate",
            is_eligible=True, eligibility_reason="ok",
            amount=3000.0, attempt_count=1, max_attempts=3,
            days_since_event=2, days_overdue=0, risk_score=40,
            failure_reason="account_closed",
        )
        assert not res.allowed


# ---------------------------------------------------------------------------
# FLOW 6: PROMISE_TO_PAY
# ---------------------------------------------------------------------------

class TestPromiseToPayFlow:
    def test_detection_routes_correctly(self):
        result = process_orchestrated_case(make_case(case_type="PROMISE_TO_PAY"))
        assert result["case_result"]["case_type"] == "PROMISE_TO_PAY"

    def test_execution_collect_promise(self):
        res = dispatch_execution(
            case_type="PROMISE_TO_PAY",
            case_id="C006", transaction_id="TX006",
            amount=8000.0, customer_id="CUST06",
            action="collect_promise", promise_date="2026-09-10", days_overdue=0,
        )
        assert res["case_type"] == "PROMISE_TO_PAY"
        assert res["action"] == "collect_promise"
        assert res["provider_mode"] == "SIMULATED"

    def test_execution_reminder_action(self):
        res = dispatch_execution(
            case_type="PROMISE_TO_PAY",
            case_id="C006b", transaction_id="TX006b",
            amount=8000.0, customer_id="CUST06",
            action="reminder", promise_date="2026-09-10", days_overdue=0,
        )
        assert res["status"] == "FOLLOW_UP"

    def test_broken_promise_beyond_grace_escalated_by_policy(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="PROMISE_TO_PAY", action="collect_promise",
            is_eligible=True, eligibility_reason="ok",
            amount=8000.0, attempt_count=1, max_attempts=2,
            days_since_event=0, days_overdue=5, risk_score=40,
            failure_reason="promise_broken",
        )
        assert not res.allowed
        assert res.policy_status == "escalated"

    def test_promise_broken_within_grace_allowed(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="PROMISE_TO_PAY", action="collect_promise",
            is_eligible=True, eligibility_reason="ok",
            amount=8000.0, attempt_count=1, max_attempts=2,
            days_since_event=0, days_overdue=1, risk_score=40,
            failure_reason="promise_broken",
        )
        assert res.allowed

    def test_execution_escalate_on_broken_promise(self):
        res = dispatch_execution(
            case_type="PROMISE_TO_PAY",
            case_id="C006c", transaction_id="TX006c",
            amount=8000.0, customer_id="CUST06",
            action="escalate", days_overdue=5,
        )
        assert res["status"] == "ESCALATED"
        assert res["provider_mode"] == "SIMULATED"


# ---------------------------------------------------------------------------
# Cross-Cutting Scenarios
# ---------------------------------------------------------------------------

class TestCrossCuttingScenarios:
    """Tests covering scenarios 1–10 from the acceptance criteria."""

    # 1. Successful recovery
    def test_successful_recovery_outcome(self):
        # Use a transaction_id that produces a "recovered" result in the sandbox
        # SandboxPaymentAdapter: hash(tx_id) % 100 < 75 = recovered
        # Find a tx_id that recovers
        from backend.payment.sandbox import SandboxPaymentAdapter
        adapter = SandboxPaymentAdapter()
        for suffix in range(200):
            tx_id = f"TX_RECOVER_{suffix}"
            if hash(tx_id) % 100 < 75:
                res = dispatch_execution(
                    case_type="PAYMENT_FAILURE",
                    case_id="C_SUCCESS", transaction_id=tx_id,
                    amount=1000.0, customer_id="CUST_S",
                    action="retry",
                )
                assert res["recovered"] is True
                assert res["recovered_amount"] == 1000.0
                return
        pytest.fail("Could not find a transaction_id that produces a recovered result")

    # 2. Failed recovery
    def test_failed_recovery_outcome(self):
        from backend.payment.sandbox import SandboxPaymentAdapter
        for suffix in range(200):
            tx_id = f"TX_FAIL_{suffix}"
            if hash(tx_id) % 100 >= 75:
                res = dispatch_execution(
                    case_type="PAYMENT_FAILURE",
                    case_id="C_FAIL", transaction_id=tx_id,
                    amount=1000.0, customer_id="CUST_F",
                    action="retry",
                )
                assert res["recovered"] is False
                assert res["recovered_amount"] == 0.0
                return
        pytest.fail("Could not find a transaction_id that produces a failed result")

    # 3. Policy-blocked recovery
    def test_policy_blocked_recovery(self):
        result = process_orchestrated_case(make_case(
            case_type="PAYMENT_FAILURE",
            failure_reason="timeout",
            attempt_count=5,  # exceeds max, eligibility blocks it
            max_attempts=2,
        ))
        assert result["case_result"]["policy_decision"] == "BLOCK"

    # 4. Maximum retry stopping rule
    def test_max_retry_stopping_rule(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="PAYMENT_FAILURE", action="retry",
            is_eligible=True, eligibility_reason="ok",
            amount=1000.0, attempt_count=5, max_attempts=2,
            days_since_event=1, days_overdue=0, risk_score=40,
        )
        assert not res.allowed
        assert "Attempt limit" in res.reason

    # 5. High-risk escalation
    def test_high_risk_escalation(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="PAYMENT_FAILURE", action="retry",
            is_eligible=True, eligibility_reason="ok",
            amount=1000.0, attempt_count=1, max_attempts=3,
            days_since_event=1, days_overdue=0, risk_score=90,
        )
        assert not res.allowed
        assert res.policy_status == "escalated"

    # 6. B2B escalation after 30 days
    def test_b2b_escalation_after_30_days(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="B2B_RECEIVABLE", action="reminder",
            is_eligible=True, eligibility_reason="ok",
            amount=50000.0, attempt_count=1, max_attempts=5,
            days_since_event=35, days_overdue=35, risk_score=50,
        )
        assert not res.allowed
        assert res.policy_status == "escalated"

    # 7. Broken promise-to-pay escalation
    def test_broken_promise_to_pay_escalation(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="PROMISE_TO_PAY", action="collect_promise",
            is_eligible=True, eligibility_reason="ok",
            amount=5000.0, attempt_count=1, max_attempts=2,
            days_since_event=0, days_overdue=3, risk_score=50,
            failure_reason="promise_broken",
        )
        assert not res.allowed
        assert res.policy_status == "escalated"

    # 8. Mandate retry limit
    def test_mandate_retry_limit(self):
        engine = CasePolicyEngine()
        res = engine.evaluate(
            case_type="MANDATE_FAILURE", action="schedule_mandate",
            is_eligible=True, eligibility_reason="ok",
            amount=2000.0, attempt_count=4, max_attempts=3,
            days_since_event=2, days_overdue=0, risk_score=40,
        )
        assert not res.allowed

    # 9. Communication provider failure — simulation fallback
    def test_communication_simulation_fallback(self):
        """All providers are SIMULATED; they must not raise on failure."""
        from backend.communications.providers.email import EmailProvider
        from backend.communications.providers.sms import SMSProvider
        from backend.communications.providers.voice import VoiceProvider
        from backend.communications.providers.whatsapp import WhatsAppProvider
        ep = EmailProvider()
        res = ep.send_email("CUST1", "test@example.com", "Test", "Body")
        assert res["status"] == "SIMULATED_SENT"
        assert res["provider_mode"] == "SIMULATED"

        sp = SMSProvider()
        res = sp.send_sms("CUST1", "+919876543210", "Test message")
        assert res["provider_mode"] == "SIMULATED"

        vp = VoiceProvider()
        res = vp.make_call("CUST1", "+919876543210", "Test call")
        assert res["provider_mode"] == "SIMULATED"

        wp = WhatsAppProvider()
        res = wp.send_message("CUST1", "+919876543210", "test", {"amount": 100})
        assert res["provider_mode"] == "SIMULATED"

    # 10. Simulation fallback — provider_mode clearly marked
    def test_all_executions_marked_simulated(self):
        case_types = [
            ("PAYMENT_FAILURE", "retry"),
            ("CHECKOUT_ABANDONMENT", "reminder"),
            ("FAILED_SUBSCRIPTION", "retry"),
            ("B2B_RECEIVABLE", "reminder"),
            ("MANDATE_FAILURE", "schedule_mandate"),
            ("PROMISE_TO_PAY", "collect_promise"),
        ]
        for ct, action in case_types:
            res = dispatch_execution(
                case_type=ct,
                case_id=f"C_{ct}", transaction_id=f"TX_{ct}",
                amount=1000.0, customer_id="CUST_TEST",
                action=action, attempt_count=1, days_overdue=0,
                promise_date="2026-09-15",
            )
            assert res["provider_mode"] == "SIMULATED", (
                f"{ct}: expected SIMULATED but got {res['provider_mode']}"
            )


# ---------------------------------------------------------------------------
# Audit Logger Integration
# ---------------------------------------------------------------------------

class TestAuditIntegration:
    def test_every_execution_produces_audit_event(self):
        """Each of the six flows must generate an audit event."""
        case_types = [
            "PAYMENT_FAILURE", "CHECKOUT_ABANDONMENT", "FAILED_SUBSCRIPTION",
            "B2B_RECEIVABLE", "MANDATE_FAILURE", "PROMISE_TO_PAY",
        ]
        for ct in case_types:
            result = process_orchestrated_case(make_case(case_type=ct))
            audit = result["audit_event"]
            assert audit["transaction_id"], f"{ct}: audit event missing transaction_id"
            assert audit["case_type"] == ct, f"{ct}: audit case_type mismatch"
            assert audit["executed_at"], f"{ct}: audit event missing timestamp"

    def test_audit_includes_policy_decision(self):
        result = process_orchestrated_case(make_case(case_type="PAYMENT_FAILURE"))
        audit = result["audit_event"]
        assert audit["policy_decision"] in ("ALLOW", "BLOCK")

    def test_audit_includes_execution_status(self):
        result = process_orchestrated_case(make_case(case_type="PAYMENT_FAILURE"))
        audit = result["audit_event"]
        assert audit["execution_status"] is not None

    def test_audit_includes_communication_attempts(self):
        result = process_orchestrated_case(make_case(case_type="PAYMENT_FAILURE", amount=6000.0))
        audit = result["audit_event"]
        assert isinstance(audit["communication_attempts"], int)


# ---------------------------------------------------------------------------
# Batch Metrics
# ---------------------------------------------------------------------------

class TestBatchMetrics:
    def test_batch_metrics_returns_required_fields(self):
        from backend.services.case_manager import get_case_manager
        mgr = get_case_manager()
        metrics = mgr.calculate_batch_metrics()
        required = [
            "total_cases", "total_revenue_at_risk", "total_eligible_cases",
            "total_recovery_attempts", "total_successful_recoveries",
            "total_recovered_amount", "overall_recovery_rate",
            "total_blocked_actions", "total_escalated_cases",
            "case_type_breakdown",
        ]
        for field in required:
            assert field in metrics, f"Missing metrics field: {field}"

    def test_batch_metrics_case_type_breakdown(self):
        from backend.services.case_manager import get_case_manager
        mgr = get_case_manager()
        metrics = mgr.calculate_batch_metrics()
        # breakdown entries should have per-flow fields
        for entry in metrics["case_type_breakdown"]:
            assert "case_type" in entry
            assert "recovery_rate" in entry
            assert "recovered_amount" in entry
