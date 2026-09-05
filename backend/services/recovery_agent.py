from typing import Union, Dict, Any, Optional
import pandas as pd
from backend.schemas.transaction import TransactionInput
from backend.schemas.risk import RiskResult
from backend.schemas.decision import AIDecisionResult
from backend.schemas.recovery import EligibilityResult
from backend.services.preprocessing import preprocess_transaction
from backend.services.eligibility_engine import EligibilityEngine
from backend.services.risk_detector import RiskDetector


class RecoveryAgent:
    """
    Central AI Decision Engine. Analyzes transaction, eligibility, and risk signals
    to recommend a recovery action (retry, reminder, escalate, stop) with diagnosis and confidence.
    """

    def analyze(
        self,
        transaction: Union[TransactionInput, Dict[str, Any]],
        eligibility: Optional[EligibilityResult] = None,
        risk: Optional[RiskResult] = None
    ) -> AIDecisionResult:
        if not isinstance(transaction, TransactionInput):
            transaction = preprocess_transaction(transaction)

        if eligibility is None:
            eligibility = EligibilityEngine().evaluate(transaction)

        if risk is None:
            risk = RiskDetector().evaluate(transaction)

        status = transaction.payment_status
        reason = transaction.failure_reason
        attempts = transaction.attempt_count
        previous_payments = transaction.customer_previous_payments
        previous_failures = transaction.customer_previous_failures
        days_since_event = transaction.days_since_event

        # 1. Payment already successful -> stop
        if status == "success":
            return AIDecisionResult(
                action="stop",
                diagnosis="Payment already successful",
                reason="No recovery is required.",
                confidence=0.99
            )

        # 2. If eligibility engine explicitly declared ineligible, return appropriate non-retry action
        if not eligibility.eligible:
            if reason == "insufficient_funds":
                return AIDecisionResult(
                    action="escalate",
                    diagnosis="Insufficient funds",
                    reason="Immediate repeated retries could create unnecessary payment attempts.",
                    confidence=0.91
                )
            if attempts >= 3:
                return AIDecisionResult(
                    action="stop",
                    diagnosis="Retry limit reached",
                    reason="Maximum retry attempts have already been reached.",
                    confidence=0.97
                )
            if days_since_event > 14:
                return AIDecisionResult(
                    action="stop",
                    diagnosis="Stale recovery opportunity",
                    reason="The transaction is outside the recovery window.",
                    confidence=0.94
                )
            return AIDecisionResult(
                action="stop",
                diagnosis="Low recovery probability / Ineligible",
                reason=eligibility.reason,
                confidence=0.85
            )

        # 3. Checkout abandonment
        if status == "abandoned":
            if days_since_event <= 7:
                return AIDecisionResult(
                    action="reminder",
                    diagnosis="Checkout abandonment",
                    reason="Recent abandoned checkout with potential purchase intent.",
                    confidence=0.88
                )
            return AIDecisionResult(
                action="stop",
                diagnosis="Stale abandoned checkout",
                reason="The abandoned checkout is too old for an immediate recovery attempt.",
                confidence=0.82
            )

        # 4. Temporary technical failures
        if reason in ["timeout", "network_error", "upi_failure"]:
            if attempts <= 2 and days_since_event <= 7:
                return AIDecisionResult(
                    action="retry",
                    diagnosis="Temporary payment failure",
                    reason="Failure appears temporary and the customer has not exceeded the retry limit.",
                    confidence=0.92
                )
            return AIDecisionResult(
                action="retry",
                diagnosis="Technical payment failure retry",
                reason="System technical glitch detected with potential recovery capability.",
                confidence=0.85
            )

        # 5. Bank decline
        if reason == "bank_declined":
            if attempts <= 1 and previous_payments >= 3 and previous_failures <= 2:
                return AIDecisionResult(
                    action="retry",
                    diagnosis="Recoverable bank decline",
                    reason="Customer has a strong successful payment history.",
                    confidence=0.79
                )

        # Fallback default decision
        return AIDecisionResult(
            action="stop",
            diagnosis="Low recovery probability",
            reason="Available evidence does not justify another recovery attempt.",
            confidence=0.76
        )


def recommend_action(
    transaction: Union[TransactionInput, Dict[str, Any]],
    eligibility: Optional[EligibilityResult] = None,
    risk: Optional[RiskResult] = None
) -> AIDecisionResult:
    agent = RecoveryAgent()
    return agent.analyze(transaction, eligibility, risk)


def run_agent(input_file, output_file):
    dataframe = pd.read_csv(input_file)
    agent = RecoveryAgent()

    diagnoses, actions, confidences, reasons = [], [], [], []
    for _, row in dataframe.iterrows():
        res = agent.analyze(row.to_dict())
        diagnoses.append(res.diagnosis)
        actions.append(res.action)
        confidences.append(res.confidence)
        reasons.append(res.reason)

    dataframe["agent_diagnosis"] = diagnoses
    dataframe["agent_action"] = actions
    dataframe["agent_confidence"] = confidences
    dataframe["agent_reason"] = reasons

    dataframe.to_csv(output_file, index=False)
    return dataframe


if __name__ == "__main__":
    run_agent("data/risk_analysis.csv", "data/recovery_decisions.csv")
    print("AI decision analysis completed.")