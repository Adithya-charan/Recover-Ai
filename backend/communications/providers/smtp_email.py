"""
SMTP Email Provider — real email delivery via SMTP.

Activated when EMAIL_PROVIDER=smtp in environment.
Requires: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM

Test/demo safety:
  If EMAIL_TEST_RECIPIENT is set, ALL emails are redirected to that address.
  This prevents accidental bulk delivery during demos.

provider_mode:
  "TEST_CONNECTED" — EMAIL_TEST_RECIPIENT is set (all emails go to test address)
  "LIVE_CONNECTED" — no test recipient override; emails go to real addresses
"""
from __future__ import annotations

import os
import smtplib
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any


class SMTPEmailProvider:
    """Real SMTP email delivery provider."""

    PROVIDER_NAME = "smtp_email"

    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER", "")
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.from_addr = os.getenv("SMTP_FROM", self.user)
        self.test_recipient = os.getenv("EMAIL_TEST_RECIPIENT", "").strip()

        if not self.user or not self.password:
            raise ValueError(
                "SMTP credentials missing: set SMTP_USER and SMTP_PASSWORD in .env"
            )

        # Determine provider mode
        self.provider_mode = (
            "TEST_CONNECTED" if self.test_recipient else "LIVE_CONNECTED"
        )

    def send_email(
        self, customer_id: str, email: str, subject: str, body: str
    ) -> Dict[str, Any]:
        """Send an email via SMTP. Returns delivery result."""
        email_id = f"email_{uuid.uuid4().hex[:8]}"

        # Safety: redirect all emails to test recipient if configured
        actual_to = self.test_recipient if self.test_recipient else email
        redirect_note = (
            f" [REDIRECTED from {email} to test recipient]"
            if self.test_recipient
            else ""
        )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = actual_to
        msg["X-RecoverAI-CustomerID"] = customer_id
        msg["X-RecoverAI-EmailID"] = email_id

        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_addr, actual_to, msg.as_string())

            return {
                "channel": "email",
                "email_id": email_id,
                "customer_id": customer_id,
                "email": actual_to,
                "subject": subject,
                "status": "SENT",
                "provider_mode": self.provider_mode,
                "provider": self.PROVIDER_NAME,
                "delivery_message": f"Email delivered via SMTP.{redirect_note}",
            }
        except smtplib.SMTPAuthenticationError as exc:
            return {
                "channel": "email",
                "email_id": email_id,
                "customer_id": customer_id,
                "email": actual_to,
                "subject": subject,
                "status": "FAILED",
                "provider_mode": self.provider_mode,
                "provider": self.PROVIDER_NAME,
                "delivery_message": f"SMTP authentication failed: {exc}",
                "error": str(exc),
            }
        except Exception as exc:
            return {
                "channel": "email",
                "email_id": email_id,
                "customer_id": customer_id,
                "email": actual_to,
                "subject": subject,
                "status": "FAILED",
                "provider_mode": self.provider_mode,
                "provider": self.PROVIDER_NAME,
                "delivery_message": f"Email delivery failed: {exc}",
                "error": str(exc),
            }


def get_email_provider():
    """Factory: return SMTP provider if EMAIL_PROVIDER=smtp, else simulated."""
    mode = os.getenv("EMAIL_PROVIDER", "simulated").lower()
    if mode == "smtp":
        return SMTPEmailProvider()
    from backend.communications.providers.email import EmailProvider
    return EmailProvider()
