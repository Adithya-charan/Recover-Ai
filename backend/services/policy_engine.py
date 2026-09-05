from typing import Dict, Optional, Union, Any
import pandas as pd
from backend.schemas.transaction import TransactionInput
from backend.schemas.decision import AIDecisionResult
from backend.schemas.policy import PolicyResult
from backend.schemas.recovery import EligibilityResult
from backend.schemas.risk import RiskResult
from backend.services.preprocessing import preprocess_transaction
from backend.services.eligibility_engine import EligibilityEngine
from backend.services.recovery_agent import RecoveryAgent

# ---------------------------------------------------------------------------
# Case-type policy tables
# Every action used by case_orchestrator MUST be listed here.
# ---------------------------------------------------------------------------
CASE_TYPE_ALLOWED_ACTIONS: Dict[str, set] = {
    "PAYMENT_FAILURE":      {"retry", "reminder"},
    "CHECKOUT_ABANDONMENT": {"reminder"},
    "FAILED_SUBSCRIPTION":  {"retry", "reminder"},
    "B2B_RECEIVABLE":       {"reminder", "voice_call", "escalate"},
    "MANDATE_FAILURE":      {"schedule_mandate", "retry", "reminder"},
    "PROMISE_TO_PAY":       {"collect_promise", "reminder", "escalate"},
}

CASE_TYPE_MAX_ATTEMPTS: Dict[str, int] = {
    "PAYMENT_FAILURE":      2,
    "CHECKOUT_ABANDONMENT": 2,
    "FAILED_SUBSCRIPTION":  3,
    "B2B_RECEIVABLE":       5,
    "MANDATE_FAILURE":      3,
    "PROMISE_TO_PAY":       2,
}

# Days; None = no window limit
CASE_TYPE_RECOVERY_WINDOW: Dict[str, Optional[int]] = {
    "PAYMENT_FAILURE":      7,
    "CHECKOUT_ABANDONMENT": 7,
    "FAILED_SUBSCRIPTION":  30,
    "B2B_RECEIVABLE":       60,
    "MANDATE_FAILURE":      14,
    "PROMISE_TO_PAY":       None,
}


class PolicyEngine:
    """
    Independent Policy Governance Engine for the standard pipeline.
    Checks whether an AI-recommended recovery action is permitted
    according to financial and compliance safety rules.
    """

    MAX_RETRY_ATTEMPTS = 2
    MAX_RECOVERY_AMOUNT = 10_000.0
    MAX_RECOVERY_AGE_DAYS = 7
    ALLOWED_ACTIONS = {"retry", "reminder"}

    def evaluate(
        self,
        transaction: Union[TransactionInput, Dict[str, Any]],
        decision: Optional[AIDecisionResult] = None,
        eligibility: Optional[EligibilityResult] = None,
        risk: Optional[RiskResult] = None,
    ) -> PolicyResult:
        if not isinstance(transaction, TransactionInput):
            transaction = preprocess_transaction(transaction)

        if decision is None:
            decision = RecoveryAgent().analyze(transaction)
        if eligibility is None:
            eligibility = EligibilityEngine().evaluate(transaction)

        action = decision.action
        amount = transaction.amount
        attempts = transaction.attempt_count
        days_since_event = transaction.days_since_event
        status = transaction.payment_status
        is_eligible = eligibility.eligible

        if status == "success":
            return PolicyResult(allowed=False, policy_status="blocked",
                                reason="Payment is already successful.")

        if action not in self.ALLOWED_ACTIONS:
            return PolicyResult(
                allowed=False, policy_status="blocked",
                reason=f"Action '{action}' is not executable by the recovery policy.")

        if not is_eligible:
            return PolicyResult(allowed=False, policy_status="blocked",
                                reason="Transaction is not marked as recovery eligible.")

        if amount > self.MAX_RECOVERY_AMOUNT:
            return PolicyResult(
                allowed=False, policy_status="blocked",
                reason=f"Amount ₹{amount:,.2f} exceeds the ₹{self.MAX_RECOVERY_AMOUNT:,.2f} recovery limit.")

        if action == "retry" and attempts >= self.MAX_RETRY_ATTEMPTS:
            return PolicyResult(allowed=False, policy_status="blocked",
                                reason="Maximum retry attempts reached.")

        if days_since_event > self.MAX_RECOVERY_AGE_DAYS:
            return PolicyResult(
                allowed=False, policy_status="blocked",
                reason=f"Transaction is outside the {self.MAX_RECOVERY_AGE_DAYS}-day recovery window.")

        return PolicyResult(allowed=True, policy_status="allowed",
                            reason="Transaction passed all recovery policy checks.")


class CasePolicyEngine:
    """
    Case-type-aware policy engine used by the unified case orchestrator.

    Every action reaches execution ONLY after passing all rules here.
    No case_orchestrator code bypasses this engine.
    """

    MAX_RECOVERY_AMOUNT = 1_000_000.0   # ₹10 lakh hard cap
    HIGH_RISK_THRESHOLD = 85

    def evaluate(
        self,
        case_type: str,
        action: str,
        is_eligible: bool,
        eligibility_reason: str,
        amount: float,
        attempt_count: int,
        max_attempts: int,
        days_since_event: int,
        days_overdue: int,
        risk_score: int,
        failure_reason: str = "",
        promise_date: Optional[str] = None,
    ) -> PolicyResult:
        ct = case_type.upper()
        allowed_actions = CASE_TYPE_ALLOWED_ACTIONS.get(ct, {"retry", "reminder"})
        case_max = CASE_TYPE_MAX_ATTEMPTS.get(ct, max_attempts)
        window = CASE_TYPE_RECOVERY_WINDOW.get(ct)

        # Rule 1 — action whitelist (case-type specific)
        if action not in allowed_actions:
            return PolicyResult(
                allowed=False, policy_status="blocked",
                reason=(f"Action '{action}' is not permitted for {ct}. "
                        f"Allowed: {sorted(allowed_actions)}."))

        # Rule 2 — eligibility gate
        if not is_eligible:
            return PolicyResult(
                allowed=False, policy_status="blocked",
                reason=f"Case ineligible: {eligibility_reason}")

        # Rule 3 — hard amount cap
        if amount > self.MAX_RECOVERY_AMOUNT:
            return PolicyResult(
                allowed=False, policy_status="blocked",
                reason=(f"Amount ₹{amount:,.2f} exceeds automated cap "
                        f"₹{self.MAX_RECOVERY_AMOUNT:,.2f}."))

        # Rule 4 — retry / re-presentment attempt limit
        effective_max = min(max_attempts, case_max)
        if action in {"retry", "schedule_mandate", "collect_promise"}:
            if attempt_count > effective_max:
                return PolicyResult(
                    allowed=False, policy_status="blocked",
                    reason=(f"Attempt limit reached for {ct}: "
                            f"{attempt_count}/{effective_max}. Stopping rule enforced."))

        # Rule 5 — recovery window
        if window is not None and days_since_event > window:
            return PolicyResult(
                allowed=False, policy_status="blocked",
                reason=(f"{ct} recovery window is {window} days. "
                        f"Event is {days_since_event} days old."))

        # Rule 6 — high-risk escalation block
        if risk_score > self.HIGH_RISK_THRESHOLD:
            return PolicyResult(
                allowed=False, policy_status="escalated",
                reason=(f"Risk score {risk_score} exceeds threshold "
                        f"{self.HIGH_RISK_THRESHOLD}. Escalated to manual review."))

        # Rule 7 — B2B mandatory escalation (>30 days overdue, non-escalate action)
        if ct == "B2B_RECEIVABLE" and days_overdue > 30 and action != "escalate":
            return PolicyResult(
                allowed=False, policy_status="escalated",
                reason=(f"B2B overdue {days_overdue} days (>30). "
                        f"Must escalate to account management."))

        # Rule 8 — mandate irrecoverable return codes
        if ct == "MANDATE_FAILURE" and failure_reason in {"mandate_revoked", "account_closed"}:
            return PolicyResult(
                allowed=False, policy_status="blocked",
                reason=(f"Mandate return code '{failure_reason}' prohibits "
                        f"automated re-presentment."))

        # Rule 9 — broken promise beyond grace period
        if (ct == "PROMISE_TO_PAY"
                and failure_reason == "promise_broken"
                and days_overdue > 2):
            return PolicyResult(
                allowed=False, policy_status="escalated",
                reason=(f"Promise broken by {days_overdue} days (grace: 2 days). "
                        f"Escalating to collections."))

        return PolicyResult(
            allowed=True, policy_status="allowed",
            reason=f"All policy checks passed for {ct} — action '{action}' authorised.")


def evaluate_policy(
    transaction: Union[TransactionInput, Dict[str, Any]],
    decision: Optional[AIDecisionResult] = None,
    eligibility: Optional[EligibilityResult] = None,
    risk: Optional[RiskResult] = None,
) -> PolicyResult:
    return PolicyEngine().evaluate(transaction, decision, eligibility, risk)


def apply_policy(input_file: str, output_file: str):
    dataframe = pd.read_csv(input_file)
    engine = PolicyEngine()
    results = []
    for _, row in dataframe.iterrows():
        tx = preprocess_transaction(row.to_dict())
        results.append(engine.evaluate(tx))
    dataframe["policy_decision"] = ["ALLOW" if r.allowed else "BLOCK" for r in results]
    dataframe["policy_reason"] = [r.reason for r in results]
    dataframe.to_csv(output_file, index=False)
    return dataframe


if __name__ == "__main__":
    apply_policy("data/recovery_decisions.csv", "data/policy_decisions.csv")
    print("Policy evaluation completed.")
