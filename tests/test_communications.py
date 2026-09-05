import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.schemas.transaction import TransactionInput
from backend.schemas.decision import AIDecisionResult
from backend.communications.orchestrator import CommunicationOrchestrator, orchestrate_communications


class TestCommunications(unittest.TestCase):

    def setUp(self):
        self.orchestrator = CommunicationOrchestrator()

    def test_reminder_abandoned_channels(self):
        tx = TransactionInput(transaction_id="TX_COM_01", customer_id="C01", amount=500, payment_status="abandoned")
        dec = AIDecisionResult(action="reminder", diagnosis="Abandoned", reason="Reminder", confidence=0.88)
        res = self.orchestrator.dispatch(tx, dec, policy_allowed=True)
        channels = [r["channel"] for r in res]
        self.assertIn("whatsapp", channels)
        self.assertIn("email", channels)

    def test_high_value_retry_voice_whatsapp(self):
        tx = TransactionInput(transaction_id="TX_COM_02", customer_id="C02", amount=8000, payment_status="failed")
        dec = AIDecisionResult(action="retry", diagnosis="Timeout", reason="Retry", confidence=0.9)
        res = self.orchestrator.dispatch(tx, dec, policy_allowed=True)
        channels = [r["channel"] for r in res]
        self.assertIn("voice", channels)
        self.assertIn("whatsapp", channels)

    def test_standard_retry_whatsapp_sms(self):
        tx = TransactionInput(transaction_id="TX_COM_03", customer_id="C03", amount=1500, payment_status="failed")
        dec = AIDecisionResult(action="retry", diagnosis="Timeout", reason="Retry", confidence=0.9)
        res = self.orchestrator.dispatch(tx, dec, policy_allowed=True)
        channels = [r["channel"] for r in res]
        self.assertIn("whatsapp", channels)
        self.assertIn("sms", channels)


if __name__ == "__main__":
    unittest.main()
