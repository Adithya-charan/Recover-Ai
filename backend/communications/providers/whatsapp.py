import uuid
from typing import Dict, Any

SIMULATED = "SIMULATED"


class WhatsAppProvider:
    """
    WhatsApp Recovery Message Provider Adapter. Currently SIMULATED.
    """

    PROVIDER_MODE = SIMULATED
    PROVIDER_NAME = "whatsapp_simulated"

    def send_message(self, customer_id: str, phone: str, template_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        msg_id = f"wa_{uuid.uuid4().hex[:8]}"
        amount_str = f"₹{params.get('amount', 0):,.2f}"
        text = f"Your payment of {amount_str} could not be completed. Click here to retry securely."

        return {
            "channel": "whatsapp",
            "message_id": msg_id,
            "customer_id": customer_id,
            "phone": phone,
            "template": template_name,
            "status": "SIMULATED_DELIVERED",
            "provider_mode": self.PROVIDER_MODE,
            "provider": self.PROVIDER_NAME,
            "delivery_message": text,
        }
