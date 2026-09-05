from typing import Union, Dict, Any
from backend.schemas.transaction import TransactionInput
from backend.schemas.recovery import EligibilityResult
from backend.services.preprocessing import preprocess_transaction


class EligibilityEngine:
    """
    Evaluates whether a transaction is eligible to enter the RecoverAI recovery pipeline.
    Reuses existing recovery business rules from the codebase.
    """

    RECOVERABLE_FAILURES = {
        "timeout",
        "network_error",
        "upi_failure",
    }

    def evaluate(self, transaction: Union[TransactionInput, Dict[str, Any]]) -> EligibilityResult:
        if not isinstance(transaction, TransactionInput):
            transaction = preprocess_transaction(transaction)

        status = transaction.payment_status
        reason = transaction.failure_reason
        attempts = transaction.attempt_count
        prev_payments = transaction.customer_previous_payments
        prev_failures = transaction.customer_previous_failures
        days_since = transaction.days_since_event

        # Rule 1: Successful payments are never eligible for recovery.
        if status == "success":
            return EligibilityResult(
                eligible=False,
                reason="Payment is already successful; no recovery required."
            )

        # Rule 2: Maximum retry attempts protection (attempt_count >= 3)
        if attempts >= 3 and status != "abandoned":
            return EligibilityResult(
                eligible=False,
                reason="Maximum retry attempts reached (>= 3)."
            )

        # Rule 3: Abandoned checkouts are eligible if recent.
        if status == "abandoned":
            if days_since <= 30:
                return EligibilityResult(
                    eligible=True,
                    reason="Checkout abandonment with potential purchase intent."
                )
            return EligibilityResult(
                eligible=False,
                reason="Abandoned checkout is outside the active recovery window."
            )

        # Rule 4: Failed payments evaluation.
        if status == "failed":
            # Temporary technical failures
            if reason in self.RECOVERABLE_FAILURES:
                return EligibilityResult(
                    eligible=True,
                    reason=f"Recoverable technical failure ({reason})."
                )

            # Bank declines are eligible if customer has good payment history
            if reason == "bank_declined":
                if attempts <= 1 and prev_payments >= 3 and prev_failures <= 2:
                    return EligibilityResult(
                        eligible=True,
                        reason="Recoverable bank decline with strong customer payment history."
                    )
                return EligibilityResult(
                    eligible=False,
                    reason="Bank decline without sufficient positive customer payment history."
                )

            # Insufficient funds
            if reason == "insufficient_funds":
                return EligibilityResult(
                    eligible=False,
                    reason="Insufficient funds cannot be recovered via immediate retry."
                )

            # Other failure reasons (authentication_failed, etc.)
            return EligibilityResult(
                eligible=False,
                reason=f"Payment failure reason '{reason}' is not eligible for recovery."
            )

        return EligibilityResult(
            eligible=False,
            reason=f"Unsupported payment status '{status}'."
        )


def check_eligibility(transaction: Union[TransactionInput, Dict[str, Any]]) -> EligibilityResult:
    engine = EligibilityEngine()
    return engine.evaluate(transaction)
