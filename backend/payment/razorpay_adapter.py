from typing import Dict, Any
import hmac
import hashlib
import json
import os

import razorpay

from backend.payment.base import PaymentGatewayAdapter


class RazorpayAdapter(PaymentGatewayAdapter):
    """Razorpay Test-Mode adapter using the official razorpay Python SDK.

    All operations are performed against Razorpay's sandbox (test) environment.
    Credentials are read from environment variables — never hardcoded.
    RECOVERY_MODE=test selects this adapter via payment/provider.py.
    """

    PROVIDER_MODE = "TEST_CONNECTED"

    def __init__(self):
        self.key_id = os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        if not self.key_id or not self.key_secret:
            raise ValueError("Razorpay credentials not configured in environment")
        # Razorpay client automatically uses test mode when test keys are supplied.
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))

    def create_payment(self, transaction_id: str, amount: float, customer_id: str) -> Dict[str, Any]:
        """Create a Razorpay order (amount is in INR, converted to paise)."""
        amount_paise = int(round(amount * 100))
        order_data = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": transaction_id,
            "notes": {"customer_id": customer_id, "transaction_id": transaction_id},
            "payment_capture": 1,
        }
        order = self.client.order.create(order_data)
        return {
            "order_id": order.get("id"),
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "amount": amount,
            "currency": "INR",
            "status": order.get("status"),
            "environment": "test",
            "provider_mode": self.PROVIDER_MODE,
        }

    def retry_payment(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        """Fetch order status via receipt lookup.
        Razorpay test mode does not have a standalone retry API; this returns
        order status and marks 'recovered' when status is 'paid'.
        """
        orders = self.client.order.all({"receipt": transaction_id})
        items = orders.get("items") or []
        if not items:
            raise ValueError(f"No Razorpay order found for transaction {transaction_id}")
        order = items[0]
        recovered = order.get("status") == "paid"
        return {
            "order_id": order.get("id"),
            "transaction_id": transaction_id,
            "amount": amount,
            "status": order.get("status"),
            "gateway_message": f"Razorpay TEST order status: {order.get('status')}",
            "recovered": recovered,
            "environment": "test",
            "provider_mode": self.PROVIDER_MODE,
        }

    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """Fetch the order status for the given transaction id."""
        orders = self.client.order.all({"receipt": transaction_id})
        items = orders.get("items") or []
        if not items:
            return {
                "transaction_id": transaction_id,
                "status": "not_found",
                "environment": "test",
                "provider_mode": self.PROVIDER_MODE,
            }
        order = items[0]
        return {
            "order_id": order.get("id"),
            "transaction_id": transaction_id,
            "status": order.get("status"),
            "amount": (order.get("amount") or 0) / 100.0,
            "currency": order.get("currency"),
            "environment": "test",
            "provider_mode": self.PROVIDER_MODE,
        }

    def handle_webhook(self, payload: Dict[str, Any], signature: str = "") -> Dict[str, Any]:
        """Verify Razorpay webhook signature (HMAC-SHA256)."""
        if not signature:
            raise ValueError("Missing Razorpay webhook signature")
        body = json.dumps(payload, separators=(",", ":"), sort_keys=False)
        expected = hmac.new(
            self.key_secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        verified = hmac.compare_digest(expected, signature)
        event_type = payload.get("event")
        tx_id = (
            payload.get("payload", {})
            .get("payment", {})
            .get("entity", {})
            .get("notes", {})
            .get("transaction_id")
        )
        return {
            "status": "processed" if verified else "failed",
            "event": event_type,
            "transaction_id": tx_id,
            "verified": verified,
            "provider_mode": self.PROVIDER_MODE,
        }
