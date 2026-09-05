import math
from typing import Union, Dict, Any
from backend.schemas.transaction import TransactionInput
from backend.schemas.risk import RiskResult
from backend.services.preprocessing import preprocess_transaction
from backend.ml.features import extract_features


class RecoveryMLModel:
    """
    Advanced ML inference layer for RecoverAI. Calculates recovery probability,
    expected recovery value, risk score, and risk level.
    """

    MODEL_VERSION = "ml-v1"

    def predict(self, transaction: Union[TransactionInput, Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(transaction, TransactionInput):
            transaction = preprocess_transaction(transaction)

        feats = extract_features(transaction)

        amount = feats["amount"]
        attempts = feats["attempt_count"]
        days = feats["days_since_event"]
        status_enc = feats["status_encoded"]
        reason_enc = feats["reason_encoded"]
        success_ratio = feats["hist_success_ratio"]

        # Calculate recovery probability using feature weights
        base_prob = 0.50

        if status_enc == 2:  # success
            recovery_prob = 0.0
        elif status_enc == 1:  # abandoned
            recovery_prob = 0.70 - (days * 0.02)
        else:  # failed
            if reason_enc in [0, 1, 2]:  # technical
                recovery_prob = 0.80 - (attempts * 0.10)
            elif reason_enc == 3:  # bank_declined
                recovery_prob = 0.40 + (success_ratio * 0.35)
            elif reason_enc == 4:  # insufficient_funds
                recovery_prob = 0.15
            else:
                recovery_prob = 0.25

        recovery_prob = max(0.0, min(round(recovery_prob, 4), 1.0))
        expected_recovery_value = round(amount * recovery_prob, 2)

        # Calculate risk score (0-100)
        risk_score = 0
        if status_enc == 0:
            risk_score += 35
        elif status_enc == 1:
            risk_score += 25

        if reason_enc in [0, 1, 2, 3]:
            risk_score += 20

        if amount >= 2000:
            risk_score += 15

        if success_ratio >= 0.6:
            risk_score += 10

        if attempts >= 3:
            risk_score -= 15

        if days > 14:
            risk_score -= 15

        risk_score = max(0, min(risk_score, 100))

        if risk_score >= 70:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "recovery_probability": recovery_prob,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "expected_recovery_value": expected_recovery_value,
            "model_version": self.MODEL_VERSION
        }
