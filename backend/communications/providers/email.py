import uuid
from typing import Dict, Any


# Provider mode constants
SIMULATED = "SIMULATED"
TEST_CONNECTED = "TEST_CONNECTED"
LIVE_CONNECTED = "LIVE_CONNECTED"


class EmailProvider:
    """
    Email Recovery Delivery Provider Adapter.
    Currently SIMULATED — no real SMTP connection is made.
    """

    PROVIDER_MODE = SIMULATED
    PROVIDER_NAME = "email_simulated"

    def send_email(self, customer_id: str, email: str, subject: str, body: str) -> Dict[str, Any]:
        email_id = f"email_{uuid.uuid4().hex[:8]}"
        return {
            "channel": "email",
            "email_id": email_id,
            "customer_id": customer_id,
            "email": email,
            "subject": subject,
            "status": "SIMULATED_SENT",
            "provider_mode": self.PROVIDER_MODE,
            "provider": self.PROVIDER_NAME,
            "delivery_message": "Email notification simulated (no real SMTP connection).",
        }
