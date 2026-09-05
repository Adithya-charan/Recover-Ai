"""
Tests for RazorpayAdapter (Phase 5).

Uses mocked Razorpay client so no real API calls are made.
Verifies:
- Correct inheritance from PaymentGatewayAdapter
- RECOVERY_MODE=test selects RazorpayAdapter
- RECOVERY_MODE=simulation selects SandboxPaymentAdapter
- create_payment / retry_payment / get_payment_status / handle_webhook
- Webhook signature handling
- TEST MODE is clearly marked in responses
"""
import hmac
import hashlib
import json
import os
import pytest
from unittest.mock import MagicMock, patch

from backend.payment.base import PaymentGatewayAdapter
from backend.payment.sandbox import SandboxPaymentAdapter


class TestRazorpayAdapterInheritance:
    def test_inherits_from_payment_gateway_adapter(self):
        from backend.payment.razorpay_adapter import RazorpayAdapter
        assert issubclass(RazorpayAdapter, PaymentGatewayAdapter)

    def test_instantiation_fails_without_credentials(self):
        from backend.payment.razorpay_adapter import RazorpayAdapter
        with patch.dict(os.environ, {"RAZORPAY_KEY_ID": "", "RAZORPAY_KEY_SECRET": ""}, clear=False):
            # Remove key env vars
            env = {k: v for k, v in os.environ.items()
                   if k not in ("RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET")}
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(ValueError, match="credentials"):
                    RazorpayAdapter()


class TestRazorpayAdapterOperations:
    @pytest.fixture
    def adapter(self):
        from backend.payment.razorpay_adapter import RazorpayAdapter
        mock_client = MagicMock()
        with patch.dict(os.environ, {
            "RAZORPAY_KEY_ID": "rzp_test_abc123",
            "RAZORPAY_KEY_SECRET": "test_secret_xyz",
        }):
            with patch("backend.payment.razorpay_adapter.razorpay.Client", return_value=mock_client):
                inst = RazorpayAdapter()
                inst._mock_client = mock_client
        return inst

    def test_create_payment_returns_order(self, adapter):
        adapter.client.order.create.return_value = {
            "id": "order_test_abc",
            "status": "created",
        }
        result = adapter.create_payment("TX_RAZ_01", 1999.0, "CUST01")
        assert result["order_id"] == "order_test_abc"
        assert result["transaction_id"] == "TX_RAZ_01"
        assert result["amount"] == 1999.0
        assert result["environment"] == "test"
        assert result["provider_mode"] == "TEST_CONNECTED"

    def test_create_payment_converts_to_paise(self, adapter):
        adapter.client.order.create.return_value = {"id": "order_x", "status": "created"}
        adapter.create_payment("TX_RAZ_02", 500.50, "CUST02")
        call_args = adapter.client.order.create.call_args[0][0]
        # 500.50 * 100 = 50050 paise
        assert call_args["amount"] == 50050

    def test_retry_payment_recovered_when_paid(self, adapter):
        adapter.client.order.all.return_value = {
            "items": [{"id": "order_paid", "status": "paid"}]
        }
        result = adapter.retry_payment("TX_RAZ_03", 1999.0)
        assert result["recovered"] is True
        assert result["environment"] == "test"
        assert result["provider_mode"] == "TEST_CONNECTED"

    def test_retry_payment_not_recovered_when_created(self, adapter):
        adapter.client.order.all.return_value = {
            "items": [{"id": "order_created", "status": "created"}]
        }
        result = adapter.retry_payment("TX_RAZ_04", 1999.0)
        assert result["recovered"] is False

    def test_retry_payment_raises_when_no_order(self, adapter):
        adapter.client.order.all.return_value = {"items": []}
        with pytest.raises(ValueError):
            adapter.retry_payment("TX_NOT_FOUND", 1000.0)

    def test_get_payment_status_found(self, adapter):
        adapter.client.order.all.return_value = {
            "items": [{"id": "order_status", "status": "captured", "amount": 199900, "currency": "INR"}]
        }
        result = adapter.get_payment_status("TX_RAZ_05")
        assert result["status"] == "captured"
        assert result["amount"] == 1999.0
        assert result["environment"] == "test"

    def test_get_payment_status_not_found(self, adapter):
        adapter.client.order.all.return_value = {"items": []}
        result = adapter.get_payment_status("TX_MISSING")
        assert result["status"] == "not_found"

    def test_handle_webhook_verified(self, adapter):
        payload = {"event": "payment.captured", "payload": {"payment": {"entity": {"notes": {"transaction_id": "TX_WH_01"}}}}}
        body = json.dumps(payload, separators=(",", ":"), sort_keys=False)
        sig = hmac.new(b"test_secret_xyz", body.encode(), hashlib.sha256).hexdigest()
        result = adapter.handle_webhook(payload, sig)
        assert result["verified"] is True
        assert result["event"] == "payment.captured"
        assert result["transaction_id"] == "TX_WH_01"
        assert result["provider_mode"] == "TEST_CONNECTED"

    def test_handle_webhook_wrong_signature(self, adapter):
        payload = {"event": "payment.captured"}
        result = adapter.handle_webhook(payload, "wrong_signature")
        assert result["verified"] is False
        assert result["status"] == "failed"

    def test_handle_webhook_missing_signature_raises(self, adapter):
        with pytest.raises(ValueError, match="signature"):
            adapter.handle_webhook({"event": "test"}, "")


class TestPaymentProviderSelection:
    def test_simulation_mode_returns_sandbox(self):
        with patch.dict(os.environ, {"RECOVERY_MODE": "simulation"}):
            from backend.payment.provider import get_payment_provider
            provider = get_payment_provider()
            assert isinstance(provider, SandboxPaymentAdapter)

    def test_test_mode_with_credentials_returns_razorpay(self):
        with patch.dict(os.environ, {
            "RECOVERY_MODE": "test",
            "RAZORPAY_KEY_ID": "rzp_test_abc",
            "RAZORPAY_KEY_SECRET": "test_secret",
        }):
            mock_client = MagicMock()
            with patch("backend.payment.razorpay_adapter.razorpay.Client", return_value=mock_client):
                from backend.payment import provider as prov_module
                import importlib
                importlib.reload(prov_module)
                p = prov_module.get_payment_provider()
                from backend.payment.razorpay_adapter import RazorpayAdapter
                assert isinstance(p, RazorpayAdapter)

    def test_sandbox_provider_mode_is_simulated(self):
        adapter = SandboxPaymentAdapter()
        adapter.create_payment("TX_SB_01", 1000.0, "CUST01")
        result = adapter.retry_payment("TX_SB_01", 1000.0)
        assert "recovered" in result
        assert result["environment"] == "sandbox"
