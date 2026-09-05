from typing import Union, Dict, Any
import pandas as pd
from backend.schemas.transaction import TransactionInput
from backend.schemas.risk import RiskResult
from backend.services.preprocessing import preprocess_transaction

RECOVERABLE_FAILURES = {
    "timeout",
    "network_error",
    "upi_failure",
    "bank_declined",
}


class RiskDetector:
    """
    Calculates risk score (0-100), risk level (low, medium, high), confidence, and detected revenue at risk.
    """

    MODEL_VERSION = "risk-v1"

    def calculate_risk_score(self, transaction: TransactionInput) -> int:
        score = 0

        if transaction.payment_status == "failed":
            score += 30
        elif transaction.payment_status == "abandoned":
            score += 25

        if transaction.failure_reason in RECOVERABLE_FAILURES:
            score += 25

        if transaction.amount >= 2000:
            score += 10

        if transaction.customer_previous_payments >= 5:
            score += 5

        if transaction.customer_previous_failures <= 2:
            score += 5

        if transaction.attempt_count >= 3:
            score -= 15

        if transaction.days_since_event > 14:
            score -= 15

        return max(0, min(score, 100))

    def classify_risk(self, score: int) -> str:
        if score >= 70:
            return "high"
        if score >= 40:
            return "medium"
        return "low"

    def evaluate(self, transaction: Union[TransactionInput, Dict[str, Any]]) -> RiskResult:
        if not isinstance(transaction, TransactionInput):
            transaction = preprocess_transaction(transaction)

        score = self.calculate_risk_score(transaction)
        level = self.classify_risk(score)
        confidence = 0.91

        revenue_at_risk = (
            transaction.amount
            if (level in ["high", "medium"] and transaction.payment_status != "success")
            else 0.0
        )

        return RiskResult(
            risk_score=score,
            risk_level=level,
            confidence=confidence,
            model_version=self.MODEL_VERSION,
            detected_revenue_at_risk=revenue_at_risk
        )


def calculate_risk(transaction: Union[TransactionInput, Dict[str, Any]]) -> RiskResult:
    detector = RiskDetector()
    return detector.evaluate(transaction)


def analyze_transactions(input_file, output_file):
    dataframe = pd.read_csv(input_file)
    detector = RiskDetector()

    results = []
    for _, row in dataframe.iterrows():
        tx = preprocess_transaction(row.to_dict())
        res = detector.evaluate(tx)
        results.append(res)

    dataframe["risk_score"] = [r.risk_score for r in results]
    dataframe["risk_level"] = [r.risk_level for r in results]
    dataframe["detected_revenue_at_risk"] = [r.detected_revenue_at_risk for r in results]

    dataframe.to_csv(output_file, index=False)
    return dataframe


if __name__ == "__main__":
    analyze_transactions("data/transactions.csv", "data/risk_analysis.csv")
    print("Risk detection completed.")