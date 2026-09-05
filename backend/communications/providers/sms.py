import uuid
from typing import Dict, Any

SIMULATED = "SIMULATED"


class SMSProvider:
    """
    SMS Recovery Delivery Provider Adapter. Currently SIMULATED.
    """

    PROVIDER_MODE = SIMULATED
    PROVIDER_NAME = "sms_simulated"

    def send_sms(self, customer_id: str, phone: str, text: str) -> Dict[str, Any]:
        sms_id = f"sms_{uuid.uuid4().hex[:8]}"
        return {
            "channel": "sms",
            "sms_id": sms_id,
            "customer_id": customer_id,
            "phone": phone,
            "status": "SIMULATED_DELIVERED",
            "provider_mode": self.PROVIDER_MODE,
            "provider": self.PROVIDER_NAME,
            "delivery_message": text,
        }
