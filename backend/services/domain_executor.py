"""
Domain-specific execution adapters for each of the six recovery flows.

Each adapter produces a normalised ExecutionOutcome dict so the case
orchestrator can consume a consistent result regardless of flow type.
All adapters use sandbox / simulation by default and clearly mark the
provider_mode so callers never mistake a simulation for a real execution.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from backend.payment.provider import execute_payment_recovery

# ---------------------------------------------------------------------------
# Normalised result shape
# ---------------------------------------------------------------------------

def _outcome(
    status: str,
    action: str,
    amount: float,
    case_id: str,
    case_type: str,
    provider: str,
    provider_mode: str,       # "SIMULATED" | "TEST_CONNECTED" | "LIVE_CONNECTED"
    provider_reference: str,
    message: str,
    recovered: bool,
    recovered_amount: float = 0.0,
) -> Dict[str, Any]:
    return {
        "status": status,
        "action": action,
        "amount": amount,
        "case_id": case_id,
        "case_type": case_type,
        "provider": provider,
        "provider_mode": provider_mode,
        "provider_reference": provider_reference,
        "message": message,
        "recovered": recovered,
        "recovered_amount": recovered_amount,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


# ---------------------------------------------------------------------------
# PAYMENT_FAILURE — sandbox payment retry
# ---------------------------------------------------------------------------

def execute_payment_failure(
    case_id: str, transaction_id: str, amount: float, customer_id: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Retry a failed payment via the configured payment gateway."""
    result = execute_payment_recovery(transaction_id, amount, customer_id)
    recovered = bool(result.get("recovered"))
    return _outcome(
        status="RECOVERED" if recovered else "FAILED",
        action="retry",
        amount=amount,
        case_id=case_id,
        case_type="PAYMENT_FAILURE",
        provider=result.get("environment", "sandbox"),
        provider_mode="SIMULATED",
        provider_reference=result.get("payment_id", result.get("order_id", "")),
        message=result.get("gateway_message", "Payment retry attempted."),
        recovered=recovered,
        recovered_amount=amount if recovered else 0.0,
    )


# ---------------------------------------------------------------------------
# CHECKOUT_ABANDONMENT — send recovery reminder / payment link
# ---------------------------------------------------------------------------

def execute_checkout_abandonment(
    case_id: str, transaction_id: str, amount: float, customer_id: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Dispatch a recovery reminder for an abandoned checkout.
    Actual conversion is tracked asynchronously; this records the attempt.
    """
    ref = f"remind_{uuid.uuid4().hex[:8]}"
    return _outcome(
        status="FOLLOW_UP",
        action="reminder",
        amount=amount,
        case_id=case_id,
        case_type="CHECKOUT_ABANDONMENT",
        provider="internal_reminder",
        provider_mode="SIMULATED",
        provider_reference=ref,
        message="Recovery reminder dispatched. Conversion tracked on callback.",
        recovered=False,
        recovered_amount=0.0,
    )


# ---------------------------------------------------------------------------
# FAILED_SUBSCRIPTION — dunning retry sequence
# ---------------------------------------------------------------------------

def execute_failed_subscription(
    case_id: str, transaction_id: str, amount: float, customer_id: str,
    attempt_count: int = 1, **kwargs: Any,
) -> Dict[str, Any]:
    """
    Retry a failed subscription charge (dunning).
    Uses the sandbox payment adapter; marks the provider_mode correctly.
    """
    result = execute_payment_recovery(transaction_id, amount, customer_id)
    recovered = bool(result.get("recovered"))
    return _outcome(
        status="RECOVERED" if recovered else "DUNNING_RETRY",
        action="retry",
        amount=amount,
        case_id=case_id,
        case_type="FAILED_SUBSCRIPTION",
        provider=result.get("environment", "sandbox"),
        provider_mode="SIMULATED",
        provider_reference=result.get("payment_id", result.get("order_id", "")),
        message=(
            f"Subscription dunning attempt {attempt_count}. "
            + result.get("gateway_message", "")
        ),
        recovered=recovered,
        recovered_amount=amount if recovered else 0.0,
    )


# ---------------------------------------------------------------------------
# B2B_RECEIVABLE — invoice collection / escalation
# ---------------------------------------------------------------------------

def execute_b2b_receivable(
    case_id: str, transaction_id: str, amount: float, customer_id: str,
    action: str = "reminder", days_overdue: int = 0, **kwargs: Any,
) -> Dict[str, Any]:
    """
    Handle B2B invoice collection.  Actions: reminder (email/call outreach)
    or escalate (flag to account management).
    """
    ref = f"b2b_{uuid.uuid4().hex[:8]}"
    if action == "escalate":
        return _outcome(
            status="ESCALATED",
            action="escalate",
            amount=amount,
            case_id=case_id,
            case_type="B2B_RECEIVABLE",
            provider="account_management",
            provider_mode="SIMULATED",
            provider_reference=ref,
            message=f"Invoice ₹{amount:,.2f} escalated to account management ({days_overdue} days overdue).",
            recovered=False,
        )

    return _outcome(
        status="FOLLOW_UP",
        action=action,
        amount=amount,
        case_id=case_id,
        case_type="B2B_RECEIVABLE",
        provider="invoice_reminder",
        provider_mode="SIMULATED",
        provider_reference=ref,
        message=f"B2B collection outreach dispatched. Invoice overdue {days_overdue} days.",
        recovered=False,
    )


# ---------------------------------------------------------------------------
# MANDATE_FAILURE — mandate re-presentment / retry
# ---------------------------------------------------------------------------

def execute_mandate_failure(
    case_id: str, transaction_id: str, amount: float, customer_id: str,
    attempt_count: int = 1, **kwargs: Any,
) -> Dict[str, Any]:
    """
    Re-present a failed mandate (NACH/UPI autopay).
    Uses the sandbox payment adapter to simulate NPCI re-presentment.
    """
    result = execute_payment_recovery(transaction_id, amount, customer_id)
    recovered = bool(result.get("recovered"))
    ref = result.get("payment_id", result.get("order_id", f"mandate_{uuid.uuid4().hex[:8]}"))
    return _outcome(
        status="RECOVERED" if recovered else "MANDATE_RETRY",
        action="schedule_mandate",
        amount=amount,
        case_id=case_id,
        case_type="MANDATE_FAILURE",
        provider="npci_nach_sandbox",
        provider_mode="SIMULATED",
        provider_reference=ref,
        message=(
            f"Mandate re-presentment attempt {attempt_count}. "
            + result.get("gateway_message", "")
        ),
        recovered=recovered,
        recovered_amount=amount if recovered else 0.0,
    )


# ---------------------------------------------------------------------------
# PROMISE_TO_PAY — record promise / send reminder / escalate on breach
# ---------------------------------------------------------------------------

def execute_promise_to_pay(
    case_id: str, transaction_id: str, amount: float, customer_id: str,
    action: str = "collect_promise",
    promise_date: Optional[str] = None,
    days_overdue: int = 0,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Handle a promise-to-pay case.
    - collect_promise: attempt to collect the promised payment via sandbox.
    - reminder: send a pre-due-date reminder.
    - escalate: breach beyond grace — hand off to collections.
    """
    ref = f"ptp_{uuid.uuid4().hex[:8]}"

    if action == "escalate":
        return _outcome(
            status="ESCALATED",
            action="escalate",
            amount=amount,
            case_id=case_id,
            case_type="PROMISE_TO_PAY",
            provider="collections",
            provider_mode="SIMULATED",
            provider_reference=ref,
            message=(f"Promise broken by {days_overdue} days. "
                     f"Case escalated to collections team."),
            recovered=False,
        )

    if action == "reminder":
        return _outcome(
            status="FOLLOW_UP",
            action="reminder",
            amount=amount,
            case_id=case_id,
            case_type="PROMISE_TO_PAY",
            provider="promise_reminder",
            provider_mode="SIMULATED",
            provider_reference=ref,
            message=f"Payment reminder sent for promise date {promise_date}.",
            recovered=False,
        )

    # collect_promise — attempt actual payment
    result = execute_payment_recovery(transaction_id, amount, customer_id)
    recovered = bool(result.get("recovered"))
    return _outcome(
        status="RECOVERED" if recovered else "FAILED",
        action="collect_promise",
        amount=amount,
        case_id=case_id,
        case_type="PROMISE_TO_PAY",
        provider=result.get("environment", "sandbox"),
        provider_mode="SIMULATED",
        provider_reference=result.get("payment_id", result.get("order_id", ref)),
        message=(f"Promise payment collection attempt. "
                 + result.get("gateway_message", "")),
        recovered=recovered,
        recovered_amount=amount if recovered else 0.0,
    )


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

EXECUTORS = {
    "PAYMENT_FAILURE":      execute_payment_failure,
    "CHECKOUT_ABANDONMENT": execute_checkout_abandonment,
    "FAILED_SUBSCRIPTION":  execute_failed_subscription,
    "B2B_RECEIVABLE":       execute_b2b_receivable,
    "MANDATE_FAILURE":      execute_mandate_failure,
    "PROMISE_TO_PAY":       execute_promise_to_pay,
}


def dispatch_execution(
    case_type: str,
    case_id: str,
    transaction_id: str,
    amount: float,
    customer_id: str,
    action: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Route execution to the correct domain adapter.
    Falls back to a safe no-op if case_type is unknown.
    """
    ct = case_type.upper()
    executor = EXECUTORS.get(ct)
    if executor is None:
        return _outcome(
            status="NOT_EXECUTED",
            action=action,
            amount=amount,
            case_id=case_id,
            case_type=ct,
            provider="none",
            provider_mode="SIMULATED",
            provider_reference="",
            message=f"Unknown case type '{ct}'. Execution skipped.",
            recovered=False,
        )

    return executor(
        case_id=case_id,
        transaction_id=transaction_id,
        amount=amount,
        customer_id=customer_id,
        action=action,
        **kwargs,
    )
