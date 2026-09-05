from abc import ABC, abstractmethod
from typing import Dict, Any


class PaymentGatewayAdapter(ABC):
    """
    Abstract Payment Gateway Adapter Interface.
    Enforces standardized contracts across Simulation, Sandbox, and Gateway integrations.
    """

    @abstractmethod
    def create_payment(self, transaction_id: str, amount: float, customer_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def retry_payment(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def handle_webhook(self, payload: Dict[str, Any], signature: str = "") -> Dict[str, Any]:
        pass
