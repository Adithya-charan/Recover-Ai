import math
from typing import Dict, Any, Union
from backend.schemas.transaction import TransactionInput


def preprocess_transaction(transaction: Union[TransactionInput, Dict[str, Any]]) -> TransactionInput:
    """
    Validates and normalizes input transaction data into a clean TransactionInput schema object.
    Does not mutate the original input dictionary/model.
    """
    if isinstance(transaction, TransactionInput):
        data = transaction.dict()
    elif isinstance(transaction, dict):
        data = transaction.copy()
    else:
        data = {}

    # Standardize string fields
    t_id = str(data.get("transaction_id") or "UNKNOWN").strip()
    c_id = str(data.get("customer_id") or "UNKNOWN").strip()

    raw_status = data.get("payment_status")
    status = str(raw_status).strip().lower() if raw_status and isinstance(raw_status, str) else "failed"
    if status not in ["success", "failed", "abandoned"]:
        status = "failed"

    raw_reason = data.get("failure_reason")
    reason = str(raw_reason).strip().lower() if raw_reason and isinstance(raw_reason, str) else "unknown"

    raw_sub = data.get("subscription_status")
    sub_status = str(raw_sub).strip().lower() if raw_sub and isinstance(raw_sub, str) else "not_applicable"

    # Numeric conversion with safety checks
    def safe_float(v, default=0.0):
        if v is None or v == "":
            return default
        try:
            val = float(v)
            if math.isnan(val) or math.isinf(val):
                return default
            return max(0.0, val)
        except (ValueError, TypeError):
            return default

    def safe_int(v, default=0):
        if v is None or v == "":
            return default
        try:
            val = float(v)
            if math.isnan(val) or math.isinf(val):
                return default
            return max(0, int(val))
        except (ValueError, TypeError):
            return default

    amount = safe_float(data.get("amount"), 0.0)
    attempts = safe_int(data.get("attempt_count"), 1)
    prev_payments = safe_int(data.get("customer_previous_payments"), 0)
    prev_failures = safe_int(data.get("customer_previous_failures"), 0)
    days_since = safe_int(data.get("days_since_event"), 0)

    clean_data = {
        "transaction_id": t_id,
        "customer_id": c_id,
        "amount": amount,
        "payment_status": status,
        "failure_reason": reason,
        "attempt_count": attempts,
        "customer_previous_payments": prev_payments,
        "customer_previous_failures": prev_failures,
        "days_since_event": days_since,
        "subscription_status": sub_status,
    }

    return TransactionInput(**clean_data)
