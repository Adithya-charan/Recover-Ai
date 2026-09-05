"""
Tests for communication providers (Phase 6 & 7).

Verifies:
- All providers return provider_mode field
- SIMULATED providers never return fake real delivery IDs
- SMTP provider factory logic
- provider_mode values are from the defined set
"""
import os
import pytest
from unittest.mock import patch, MagicMock

VALID_PROVIDER_MODES = {"SIMULATED", "TEST_CONNECTED", "LIVE_CONNECTED"}


class TestSimulatedProviders:
    def test_email_provider_mode(self):
        from backend.communications.providers.email import EmailProvider
        p = EmailProvider()
        res = p.send_email("C01", "test@test.com", "Subject", "Body")
        assert res["provider_mode"] == "SIMULATED"
        assert res["status"] == "SIMULATED_SENT"
        assert res["provider_mode"] in VALID_PROVIDER_MODES

    def test_sms_provider_mode(self):
        from backend.communications.providers.sms import SMSProvider
        p = SMSProvider()
        res = p.send_sms("C01", "+91987654", "Test SMS")
        assert res["provider_mode"] == "SIMULATED"
        assert res["status"] == "SIMULATED_DELIVERED"

    def test_voice_provider_mode(self):
        from backend.communications.providers.voice import VoiceProvider
        p = VoiceProvider()
        res = p.make_call("C01", "+91987654", "Test call")
        assert res["provider_mode"] == "SIMULATED"
        assert res["status"] == "SIMULATED_COMPLETED"

    def test_whatsapp_provider_mode(self):
        from backend.communications.providers.whatsapp import WhatsAppProvider
        p = WhatsAppProvider()
        res = p.send_message("C01", "+91987654", "template", {"amount": 1000})
        assert res["provider_mode"] == "SIMULATED"
        assert res["status"] == "SIMULATED_DELIVERED"

    def test_simulated_providers_have_provider_name(self):
        from backend.communications.providers.email import EmailProvider
        from backend.communications.providers.sms import SMSProvider
        from backend.communications.providers.voice import VoiceProvider
        from backend.communications.providers.whatsapp import WhatsAppProvider
        for cls, method, args in [
            (EmailProvider, "send_email", ("C", "e@e.com", "S", "B")),
            (SMSProvider, "send_sms", ("C", "+1", "msg")),
            (VoiceProvider, "make_call", ("C", "+1", "msg")),
            (WhatsAppProvider, "send_message", ("C", "+1", "tpl", {})),
        ]:
            res = getattr(cls(), method)(*args)
            assert "provider" in res, f"{cls.__name__} missing 'provider' key"


class TestSMTPEmailFactory:
    def test_factory_returns_simulated_when_not_configured(self):
        with patch.dict(os.environ, {"EMAIL_PROVIDER": "simulated"}):
            from backend.communications.providers.smtp_email import get_email_provider
            p = get_email_provider()
            from backend.communications.providers.email import EmailProvider
            assert isinstance(p, EmailProvider)

    def test_factory_returns_smtp_when_configured(self):
        env = {
            "EMAIL_PROVIDER": "smtp",
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@test.com",
            "SMTP_PASSWORD": "password123",
            "SMTP_FROM": "user@test.com",
            "EMAIL_TEST_RECIPIENT": "safe@test.com",
        }
        with patch.dict(os.environ, env):
            from backend.communications.providers.smtp_email import get_email_provider, SMTPEmailProvider
            p = get_email_provider()
            assert isinstance(p, SMTPEmailProvider)

    def test_smtp_provider_mode_test_connected_with_test_recipient(self):
        env = {
            "EMAIL_PROVIDER": "smtp",
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@test.com",
            "SMTP_PASSWORD": "password123",
            "EMAIL_TEST_RECIPIENT": "safe@test.com",
        }
        with patch.dict(os.environ, env):
            from backend.communications.providers.smtp_email import SMTPEmailProvider
            p = SMTPEmailProvider()
            assert p.provider_mode == "TEST_CONNECTED"

    def test_smtp_provider_mode_live_without_test_recipient(self):
        env = {
            "EMAIL_PROVIDER": "smtp",
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@test.com",
            "SMTP_PASSWORD": "password123",
            "EMAIL_TEST_RECIPIENT": "",
        }
        with patch.dict(os.environ, env):
            from backend.communications.providers.smtp_email import SMTPEmailProvider
            p = SMTPEmailProvider()
            assert p.provider_mode == "LIVE_CONNECTED"

    def test_smtp_send_email_redirects_to_test_recipient(self):
        env = {
            "EMAIL_PROVIDER": "smtp",
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@test.com",
            "SMTP_PASSWORD": "password123",
            "EMAIL_TEST_RECIPIENT": "safe@test.com",
        }
        with patch.dict(os.environ, env):
            from backend.communications.providers.smtp_email import SMTPEmailProvider
            import smtplib
            mock_smtp = MagicMock()
            mock_smtp_instance = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_smtp_instance)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            with patch("backend.communications.providers.smtp_email.smtplib.SMTP", mock_smtp):
                p = SMTPEmailProvider()
                result = p.send_email("CUST01", "real@customer.com", "Subject", "Body")
            # Email should be sent to test recipient, not real customer
            assert result["email"] == "safe@test.com"
            assert result["status"] == "SENT"
            assert result["provider_mode"] == "TEST_CONNECTED"

    def test_smtp_send_failure_returns_failed_status(self):
        env = {
            "EMAIL_PROVIDER": "smtp",
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@test.com",
            "SMTP_PASSWORD": "password123",
            "EMAIL_TEST_RECIPIENT": "safe@test.com",
        }
        with patch.dict(os.environ, env):
            from backend.communications.providers.smtp_email import SMTPEmailProvider
            import smtplib
            with patch("backend.communications.providers.smtp_email.smtplib.SMTP",
                       side_effect=ConnectionRefusedError("Connection refused")):
                p = SMTPEmailProvider()
                result = p.send_email("CUST01", "real@customer.com", "Subject", "Body")
            assert result["status"] == "FAILED"
            assert "error" in result


class TestSMTPSafety:
    """Targeted SMTP safety and NOT_CONFIGURED tests."""

    def test_smtp_not_configured_returns_simulated_provider(self):
        """When EMAIL_PROVIDER != smtp the factory returns the simulated EmailProvider."""
        with patch.dict(os.environ, {"EMAIL_PROVIDER": "simulated"}):
            import importlib
            import backend.communications.providers.smtp_email as smtp_mod
            importlib.reload(smtp_mod)
            from backend.communications.providers.email import EmailProvider
            p = smtp_mod.get_email_provider()
            assert isinstance(p, EmailProvider)
            assert p.PROVIDER_MODE == "SIMULATED"

    def test_smtp_missing_credentials_raises(self):
        """SMTPEmailProvider must raise ValueError if credentials are missing."""
        env = {"SMTP_USER": "", "SMTP_PASSWORD": ""}
        with patch.dict(os.environ, env, clear=False):
            # Temporarily remove creds from env
            stripped = {k: v for k, v in os.environ.items()
                        if k not in ("SMTP_USER", "SMTP_PASSWORD")}
            with patch.dict(os.environ, stripped, clear=True):
                from backend.communications.providers.smtp_email import SMTPEmailProvider
                with pytest.raises(ValueError, match="credentials"):
                    SMTPEmailProvider()

    def test_smtp_success_returns_sent_status(self):
        """Successful SMTP send must return status=SENT with provider_mode set."""
        env = {
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@test.com",
            "SMTP_PASSWORD": "password123",
            "EMAIL_TEST_RECIPIENT": "safe@test.com",
        }
        with patch.dict(os.environ, env):
            from backend.communications.providers.smtp_email import SMTPEmailProvider
            mock_server = MagicMock()
            smtp_ctx = MagicMock()
            smtp_ctx.__enter__ = MagicMock(return_value=mock_server)
            smtp_ctx.__exit__ = MagicMock(return_value=False)
            with patch("backend.communications.providers.smtp_email.smtplib.SMTP",
                       return_value=smtp_ctx):
                p = SMTPEmailProvider()
                result = p.send_email("CUST01", "real@customer.com", "Hello", "Body text")
        assert result["status"] == "SENT"
        assert result["provider_mode"] in ("TEST_CONNECTED", "LIVE_CONNECTED")
        assert "email_id" in result

    def test_smtp_test_recipient_overrides_real_address(self):
        """When EMAIL_TEST_RECIPIENT is set, the actual 'to' must be the test address."""
        env = {
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@test.com",
            "SMTP_PASSWORD": "password123",
            "EMAIL_TEST_RECIPIENT": "tester@safe.com",
        }
        with patch.dict(os.environ, env):
            from backend.communications.providers.smtp_email import SMTPEmailProvider
            captured = {}
            def fake_smtp(host, port, timeout=10):
                ctx = MagicMock()
                ctx.__enter__ = lambda s: mock_server
                ctx.__exit__ = MagicMock(return_value=False)
                return ctx
            mock_server = MagicMock()
            with patch("backend.communications.providers.smtp_email.smtplib.SMTP", side_effect=fake_smtp):
                p = SMTPEmailProvider()
                result = p.send_email("CUST_X", "donotuse@real.com", "Subj", "Body")
        # Must be redirected to test recipient, never the real customer address
        assert result["email"] == "tester@safe.com"
        assert result["email"] != "donotuse@real.com"

    def test_simulated_email_never_has_real_smtp_status(self):
        """Simulated EmailProvider must not return SENT — only SIMULATED_SENT."""
        from backend.communications.providers.email import EmailProvider
        p = EmailProvider()
        result = p.send_email("C", "any@any.com", "S", "B")
        assert result["status"] == "SIMULATED_SENT"
        assert result["status"] != "SENT"
        assert result["provider_mode"] == "SIMULATED"

    def test_smtp_auth_failure_returns_failed_not_raises(self):
        """SMTPAuthenticationError must return status=FAILED, not raise."""
        import smtplib
        env = {
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@test.com",
            "SMTP_PASSWORD": "wrongpassword",
            "EMAIL_TEST_RECIPIENT": "safe@test.com",
        }
        with patch.dict(os.environ, env):
            from backend.communications.providers.smtp_email import SMTPEmailProvider
            with patch(
                "backend.communications.providers.smtp_email.smtplib.SMTP",
                side_effect=smtplib.SMTPAuthenticationError(535, b"Auth failed"),
            ):
                p = SMTPEmailProvider()
                result = p.send_email("CUST02", "real@cust.com", "Subj", "Body")
        assert result["status"] == "FAILED"
        assert "error" in result
