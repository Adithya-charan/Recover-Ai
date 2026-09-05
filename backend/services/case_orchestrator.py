from typing import Union, Dict, Any, List, Optional
from datetime import datetime

from backend.schemas.case import RecoveryCaseInput, RecoveryCaseResult
from backend.schemas.transaction import TransactionInput
from backend.schemas.recovery import EligibilityResult
from backend.schemas.risk import RiskResult
from backend.schemas.decision import AIDecisionResult
from backend.schemas.policy import PolicyResult
from backend.schemas.execution import ExecutionResult

from backend.services.preprocessing import preprocess_transaction
from backend.services.eligibility_engine import EligibilityEngine
from backend.ml.inference import predict_recovery_ml
from backend.llm.model_adapter import LLMDecisionAdapter
from backend.services.policy_engine import CasePolicyEngine
from backend.services.domain_executor import dispatch_execution
from backend.communications.orchestrator import CommunicationOrchestrator
from backend.services.audit_logger import AuditLogger


VALID_CASE_TYPES = {
    "PAYMENT_FAILURE",
    "CHECKOUT_ABANDONMENT",
    "FAILED_SUBSCRIPTION",
    "B2B_RECEIVABLE",
    "MANDATE_FAILURE",
    "PROMISE_TO_PAY"
}


class UnifiedCaseOrchestrator:
    """
    Unified Case Orchestrator supporting all 6 Core Revenue-Recovery Scenarios:
    PAYMENT_FAILURE | CHECKOUT_ABANDONMENT | FAILED_SUBSCRIPTION | B2B_RECEIVABLE | MANDATE_FAILURE | PROMISE_TO_PAY

    Architecture Pipeline:
    Case Input → Domain Detection → Revenue Risk Calc → Eligibility Engine → ML Risk Model → LLM Diagnosis → Policy Governance → Execution Sandbox → Multi-Channel Comms → Outcome Tracking → Audit Logging
    """

    def __init__(self):
        self.eligibility_engine = EligibilityEngine()
        self.llm_adapter = LLMDecisionAdapter()
        self.case_policy_engine = CasePolicyEngine()
        self.communication_orchestrator = CommunicationOrchestrator()
        self.audit_logger = AuditLogger()

    def process_case(self, case_input: Union[RecoveryCaseInput, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(case_input, dict):
            c_dict = case_input
        else:
            c_dict = case_input.dict()

        case_id = c_dict.get("case_id") or f"CASE_{c_dict.get('case_type', 'PF')[:2]}_{int(datetime.utcnow().timestamp())}"
        case_type = str(c_dict.get("case_type", "PAYMENT_FAILURE")).upper()
        if case_type not in VALID_CASE_TYPES:
            case_type = "PAYMENT_FAILURE"

        customer_id = str(c_dict.get("customer_id", "CUST_DEFAULT"))
        amount = float(c_dict.get("amount", 1000.0))
        revenue_at_risk = float(c_dict.get("revenue_at_risk") or amount)
        attempt_count = int(c_dict.get("attempt_count", 1))
        max_attempts = int(c_dict.get("max_attempts", 3 if case_type != "CHECKOUT_ABANDONMENT" else 2))
        days_since_event = int(c_dict.get("days_since_event", 0))
        days_overdue = int(c_dict.get("days_overdue", 0))
        failure_reason = c_dict.get("failure_reason") or "payment_failed"
        payment_status = c_dict.get("payment_status") or "failed"
        promise_date = c_dict.get("promise_date")

        # 1. Preprocessing as TransactionInput for existing models
        tx_data = {
            "transaction_id": c_dict.get("transaction_id") or case_id,
            "customer_id": customer_id,
            "amount": amount,
            "payment_status": payment_status,
            "failure_reason": failure_reason,
            "attempt_count": attempt_count,
            "days_since_event": days_since_event,
            "customer_previous_payments": c_dict.get("customer_previous_payments", 3),
            "customer_previous_failures": c_dict.get("customer_previous_failures", 1),
            "subscription_status": c_dict.get("subscription_status", "active")
        }
        tx = preprocess_transaction(tx_data)

        # 2. Domain-Specific Eligibility Logic
        is_eligible = True
        eligibility_reason = f"Case type {case_type} eligible for AI recovery."

        if case_type == "PAYMENT_FAILURE":
            if attempt_count > max_attempts:
                is_eligible = False
                eligibility_reason = f"Attempt count {attempt_count} exceeds max limit {max_attempts}."
            elif failure_reason in ["authentication_failed", "stolen_card"]:
                is_eligible = False
                eligibility_reason = f"Failure reason '{failure_reason}' un-retryable via automated workflow."

        elif case_type == "CHECKOUT_ABANDONMENT":
            if days_since_event > 7:
                is_eligible = False
                eligibility_reason = f"Abandonment age {days_since_event} days exceeds 7-day cutoff."
            elif attempt_count >= max_attempts:
                is_eligible = False
                eligibility_reason = f"Max reminder attempts reached ({attempt_count}/{max_attempts})."

        elif case_type == "FAILED_SUBSCRIPTION":
            if c_dict.get("subscription_status") == "canceled":
                is_eligible = False
                eligibility_reason = "Subscription already canceled."
            elif attempt_count > max_attempts:
                is_eligible = False
                eligibility_reason = f"Dunning retry limit reached ({attempt_count}/{max_attempts})."

        elif case_type == "B2B_RECEIVABLE":
            if days_overdue > 60:
                is_eligible = False
                eligibility_reason = f"Overdue age {days_overdue} days exceeds 60-day automated recovery window."
            elif failure_reason == "legal_dispute":
                is_eligible = False
                eligibility_reason = "Account under legal dispute. Automated outreach suspended."

        elif case_type == "MANDATE_FAILURE":
            if failure_reason in ["mandate_revoked", "account_closed"]:
                is_eligible = False
                eligibility_reason = f"Mandate return code '{failure_reason}' prohibits automated re-presentment."
            elif attempt_count >= max_attempts:
                is_eligible = False
                eligibility_reason = f"NPCI mandate re-presentment limit reached ({attempt_count}/{max_attempts})."

        elif case_type == "PROMISE_TO_PAY":
            if failure_reason == "promise_broken" and days_overdue > 2:
                is_eligible = False
                eligibility_reason = f"Promise date broken by {days_overdue} days (> 2 days grace period)."

        eligibility = EligibilityResult(eligible=is_eligible, reason=eligibility_reason)

        # 3. Advanced ML Risk Scoring
        ml_res = predict_recovery_ml(tx)
        risk_score = ml_res["risk_score"]
        risk_level = ml_res["risk_level"]
        risk = RiskResult(
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=ml_res["recovery_probability"],
            model_version=ml_res["model_version"],
            detected_revenue_at_risk=revenue_at_risk
        )

        # 4. LLM Diagnosis & Intervention Recommendation
        llm_decision = self.llm_adapter.generate_decision(tx, eligibility=eligibility, risk=risk)

        # Determine domain-appropriate action from LLM result
        rec_action = llm_decision.action
        if not is_eligible:
            rec_action = "escalate" if risk_level == "high" else "stop"
        elif case_type == "CHECKOUT_ABANDONMENT":
            rec_action = "reminder"
        elif case_type == "B2B_RECEIVABLE":
            rec_action = "voice_call" if days_overdue >= 15 else "reminder"
        elif case_type == "MANDATE_FAILURE":
            rec_action = "schedule_mandate"
        elif case_type == "PROMISE_TO_PAY":
            rec_action = "collect_promise"

        # 5. Non-bypassable CasePolicyEngine Governance
        # Every action passes through here — no inline bypasses.
        policy = self.case_policy_engine.evaluate(
            case_type=case_type,
            action=rec_action,
            is_eligible=is_eligible,
            eligibility_reason=eligibility_reason,
            amount=amount,
            attempt_count=attempt_count,
            max_attempts=max_attempts,
            days_since_event=days_since_event,
            days_overdue=days_overdue,
            risk_score=risk_score,
            failure_reason=failure_reason,
            promise_date=promise_date,
        )
        policy_allowed = policy.allowed
        policy_reason = policy.reason

        # 6. Execution & Multi-Channel Communications
        exec_result = {}
        communications = []
        recovered_amount = 0.0
        exec_status = "NOT_EXECUTED"
        rec_status = "not_attempted"
        outcome = "pending"
        escalation_status = "none"
        exec_message = ""

        if not policy_allowed:
            exec_status = "BLOCKED"
            rec_status = "not_attempted"
            outcome = "blocked" if not is_eligible else "failed"
            if policy.policy_status == "escalated" or "escalate" in rec_action or days_overdue > 30:
                escalation_status = "escalated"
                outcome = "escalated"
            exec_message = f"Execution blocked by policy governance: {policy_reason}"
            exec_result = {}
        else:
            # Route to domain-specific executor
            exec_result = dispatch_execution(
                case_type=case_type,
                case_id=case_id,
                transaction_id=tx.transaction_id,
                amount=amount,
                customer_id=customer_id,
                action=rec_action,
                attempt_count=attempt_count,
                days_overdue=days_overdue,
                promise_date=promise_date,
            )
            recovered_amount = float(exec_result.get("recovered_amount", 0.0))
            exec_status = exec_result.get("status", "NOT_EXECUTED")
            rec_status = "RECOVERED" if exec_result.get("recovered") else (
                "FOLLOW_UP" if exec_status in {"FOLLOW_UP", "ESCALATED"} else "FAILED"
            )
            outcome = exec_result.get("status", "failed").upper()
            exec_message = exec_result.get("message", "")
            if exec_status == "ESCALATED":
                escalation_status = "escalated"
                outcome = "escalated"
            elif exec_result.get("recovered"):
                outcome = "RECOVERED"

            # Multi-channel communications dispatch
            communications = self.communication_orchestrator.dispatch(tx, llm_decision, policy_allowed)

        # 7. Audit Event Recording
        # Extract provider and reference from execution result
        exec_provider = exec_result.get("provider", "") if exec_result else ""
        exec_provider_ref = exec_result.get("provider_reference", "") if exec_result else ""
        comm_channels = ",".join(c.get("channel", "") for c in communications if c.get("channel")) if communications else ""

        audit_event = self.audit_logger.record_event(
            transaction_id=tx.transaction_id,
            customer_id=customer_id,
            amount=amount,
            payment_status=payment_status,
            failure_reason=failure_reason,
            risk_score=risk_score,
            risk_level=risk_level,
            agent_diagnosis=f"[{case_type}] {llm_decision.diagnosis}",
            agent_action=rec_action,
            agent_confidence=llm_decision.confidence,
            agent_reason=llm_decision.reason,
            policy_decision="ALLOW" if policy_allowed else "BLOCK",
            policy_reason=policy_reason,
            execution_status=exec_status,
            recovery_status=rec_status,
            recovered_amount=recovered_amount,
            execution_message=exec_message,
            case_type=case_type,
            communication_attempts=len(communications),
            communication_channel=comm_channels,
            provider=exec_provider,
            provider_reference=exec_provider_ref,
        )

        res_obj = RecoveryCaseResult(
            case_id=case_id,
            case_type=case_type,
            customer_id=customer_id,
            transaction_id=tx.transaction_id,
            amount=amount,
            revenue_at_risk=revenue_at_risk,
            status="completed" if outcome == "RECOVERED" else ("blocked" if not policy_allowed else "active"),
            risk_score=risk_score,
            risk_level=risk_level,
            diagnosis=f"[{case_type}] {llm_decision.diagnosis}",
            ai_recommendation=rec_action,
            ai_confidence=llm_decision.confidence,
            policy_decision="ALLOW" if policy_allowed else "BLOCK",
            policy_reason=policy_reason,
            attempt_count=attempt_count,
            max_attempts=max_attempts,
            next_action="Close Case" if outcome == "RECOVERED" else ("Manual Escalation" if escalation_status == "escalated" else "Follow-up Scheduled"),
            escalation_status=escalation_status,
            communication_status="simulated_sent" if communications else "not_sent",
            execution_status=exec_status,
            outcome=outcome,
            recovered_amount=recovered_amount,
            promise_date=promise_date,
            executed_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        )

        return {
            "case_result": res_obj.dict(),
            "ml_insights": ml_res,
            "llm_decision": llm_decision.dict() if hasattr(llm_decision, "dict") else dict(llm_decision),
            "execution_result": exec_result,
            "communications": communications,
            "audit_event": audit_event,
        }


def process_orchestrated_case(case_input: Union[RecoveryCaseInput, Dict[str, Any]]) -> Dict[str, Any]:
    orchestrator = UnifiedCaseOrchestrator()
    return orchestrator.process_case(case_input)
