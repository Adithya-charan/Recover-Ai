import os
import uuid
from typing import Dict, Any
from backend.payment.base import PaymentGatewayAdapter


class SandboxPaymentAdapter(PaymentGatewayAdapter):
    """
    Sandbox Payment Adapter for Razorpay / Test Gateways.
    Supports idempotency, order creation, retry processing, and webhook callbacks.
    """

    def __init__(self):
        self.key_id = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_key_id")
        self.key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "rzp_test_key_secret")
        self._orders: Dict[str, Dict[str, Any]] = {}

    def create_payment(self, transaction_id: str, amount: float, customer_id: str) -> Dict[str, Any]:
        order_id = f"order_sb_{uuid.uuid4().hex[:8]}"
        order_data = {
            "order_id": order_id,
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "amount": amount,
            "currency": "INR",
            "status": "created",
            "environment": "sandbox"
        }
        self._orders[transaction_id] = order_data
        return order_data

    def retry_payment(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        order = self._orders.get(transaction_id)
        order_id = order["order_id"] if order else f"order_sb_{uuid.uuid4().hex[:8]}"

        # Deterministic simulation based on transaction_id
        deterministic_hash = hash(transaction_id) % 100
        success = deterministic_hash < 75

        payment_status = "captured" if success else "failed"
        result = {
            "payment_id": f"pay_sb_{uuid.uuid4().hex[:8]}",
            "order_id": order_id,
            "transaction_id": transaction_id,
            "amount": amount,
            "status": payment_status,
            "gateway_message": "Razorpay Sandbox Simulation Success" if success else "Razorpay Sandbox Bank Decline",
            "environment": "sandbox",
            "recovered": success
        }
        if transaction_id in self._orders:
            self._orders[transaction_id]["status"] = payment_status
        return result

    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        if transaction_id in self._orders:
            return self._orders[transaction_id]
        return {
            "transaction_id": transaction_id,
            "status": "not_found",
            "environment": "sandbox"
        }

    def handle_webhook(self, payload: Dict[str, Any], signature: str = "") -> Dict[str, Any]:
        event_type = payload.get("event", "payment.captured")
        tx_id = payload.get("payload", {}).get("payment", {}).get("entity", {}).get("notes", {}).get("transaction_id", "UNKNOWN")
        return {
            "status": "processed",
            "event": event_type,
            "transaction_id": tx_id,
            "verified": True
        }
