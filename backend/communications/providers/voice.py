import os
import uuid
from typing import Dict, Any

SIMULATED = "SIMULATED"


class VoiceProvider:
    """
    Voice Call Recovery Provider Adapter. Currently SIMULATED.
    """

    PROVIDER_MODE = SIMULATED
    PROVIDER_NAME = "voice_simulated"

    def make_call(self, customer_id: str, phone: str, message: str) -> Dict[str, Any]:
        call_id = f"call_{uuid.uuid4().hex[:8]}"
        return {
            "channel": "voice",
            "call_id": call_id,
            "customer_id": customer_id,
            "phone": phone,
            "status": "SIMULATED_COMPLETED",
            "provider_mode": self.PROVIDER_MODE,
            "provider": self.PROVIDER_NAME,
            "delivery_message": "Automated IVR recovery call simulated (no real call placed).",
        }
