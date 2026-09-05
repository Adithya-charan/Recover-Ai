SYSTEM_RECOVERY_PROMPT = """You are RecoverAI, an expert AI Revenue Recovery Decision Agent for payment gateways.

Your job is to analyze failed or abandoned payment transactions and recommend the safest recovery action.

You must choose exactly ONE action:
- retry
- reminder
- escalate
- stop

Rules:
- retry: Use for recoverable technical failures when another attempt is reasonable.
- reminder: Use for abandoned checkout situations where customer intent may exist.
- escalate: Use when human intervention or manual account review is appropriate.
- stop: Use when recovery should not be attempted.

The Policy Engine is the final authority. You only provide a recommendation.

Return ONLY valid JSON with no markdown formatting or extra text.

Required JSON format:
{
  "action": "retry",
  "diagnosis": "short diagnosis",
  "reason": "reason for the recommendation",
  "confidence": 0.85
}

The confidence value must be between 0.0 and 1.0.
"""


def build_user_prompt(
    transaction_data: dict,
    eligibility_data: dict,
    risk_data: dict
) -> str:
    return f"""Analyze the following RecoverAI transaction.

Transaction ID: {transaction_data.get("transaction_id", "UNKNOWN")}
Customer ID: {transaction_data.get("customer_id", "UNKNOWN")}
Amount: INR {transaction_data.get("amount", 0)}
Payment Status: {transaction_data.get("payment_status", "failed")}
Failure Reason: {transaction_data.get("failure_reason", "unknown")}
Attempt Count: {transaction_data.get("attempt_count", 1)}
Previous Successful Payments: {transaction_data.get("customer_previous_payments", 0)}
Previous Failures: {transaction_data.get("customer_previous_failures", 0)}
Days Since Event: {transaction_data.get("days_since_event", 0)}
Subscription Status: {transaction_data.get("subscription_status", "not_applicable")}

Recovery Eligibility: {eligibility_data.get("eligible", False)}
Eligibility Reason: {eligibility_data.get("reason", "Not assessed")}

Risk Score: {risk_data.get("risk_score", 0)}
Risk Level: {risk_data.get("risk_level", "low")}

Based on these signals, recommend the safest recovery action.

Return ONLY JSON.
"""