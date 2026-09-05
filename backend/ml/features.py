from typing import Union, Dict, Any, List
import pandas as pd
import numpy as np
from backend.schemas.transaction import TransactionInput
from backend.services.preprocessing import preprocess_transaction

STATUS_MAP = {"failed": 0, "abandoned": 1, "success": 2}
REASON_MAP = {
    "timeout": 0,
    "network_error": 1,
    "upi_failure": 2,
    "bank_declined": 3,
    "insufficient_funds": 4,
    "authentication_failed": 5,
    "unknown": 6
}
SUB_MAP = {"not_applicable": 0, "active": 1, "inactive": 2, "expired": 3, "cancelled": 4}


def extract_features(transaction: Union[TransactionInput, Dict[str, Any]]) -> Dict[str, float]:
    if not isinstance(transaction, TransactionInput):
        transaction = preprocess_transaction(transaction)

    amount = float(transaction.amount)
    attempts = int(transaction.attempt_count)
    prev_payments = int(transaction.customer_previous_payments)
    prev_failures = int(transaction.customer_previous_failures)
    days_since = int(transaction.days_since_event)

    status_enc = STATUS_MAP.get(transaction.payment_status.lower(), 0)
    reason_enc = REASON_MAP.get(transaction.failure_reason.lower(), 6)
    sub_enc = SUB_MAP.get(transaction.subscription_status.lower(), 0)

    total_history = prev_payments + prev_failures
    hist_success_ratio = prev_payments / (total_history + 1.0)
    failure_attempt_ratio = prev_failures / (attempts + 1.0)

    return {
        "amount": amount,
        "attempt_count": float(attempts),
        "customer_previous_payments": float(prev_payments),
        "customer_previous_failures": float(prev_failures),
        "days_since_event": float(days_since),
        "status_encoded": float(status_enc),
        "reason_encoded": float(reason_enc),
        "sub_encoded": float(sub_enc),
        "hist_success_ratio": float(hist_success_ratio),
        "failure_attempt_ratio": float(failure_attempt_ratio)
    }


def extract_feature_vector(transaction: Union[TransactionInput, Dict[str, Any]]) -> List[float]:
    feat_dict = extract_features(transaction)
    return list(feat_dict.values())
