import os
from typing import Dict, Any
from backend.payment.sandbox import SandboxPaymentAdapter


def get_payment_provider():
    """Factory to return the appropriate payment gateway adapter.

    - ``simulation`` or ``sandbox`` → :class:`SandboxPaymentAdapter`
    - ``test`` (when Razorpay test credentials are present) → :class:`RazorpayAdapter`
    """
    mode = os.environ.get("RECOVERY_MODE", "simulation").lower()
    # If test mode is explicitly requested and Razorpay credentials are available, use the real adapter.
    if mode == "test" and os.getenv("RAZORPAY_KEY_ID") and os.getenv("RAZORPAY_KEY_SECRET"):
        from backend.payment.razorpay_adapter import RazorpayAdapter
        return RazorpayAdapter()
    # Default to sandbox simulation.
    return SandboxPaymentAdapter()


def execute_payment_recovery(transaction_id: str, amount: float, customer_id: str = "UNKNOWN") -> Dict[str, Any]:
    provider = get_payment_provider()
    provider.create_payment(transaction_id, amount, customer_id)
    return provider.retry_payment(transaction_id, amount)
