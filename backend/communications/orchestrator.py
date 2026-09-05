from typing import Union, Dict, Any, List
from backend.schemas.transaction import TransactionInput
from backend.schemas.decision import AIDecisionResult
from backend.services.preprocessing import preprocess_transaction
from backend.communications.providers.voice import VoiceProvider
from backend.communications.providers.whatsapp import WhatsAppProvider
from backend.communications.providers.email import EmailProvider
from backend.communications.providers.sms import SMSProvider
from backend.communications.templates import get_template


class CommunicationOrchestrator:
    """
    Multi-Channel Communication Recovery Orchestrator.
    Determines optimal channels (Voice, WhatsApp, Email, SMS) and dispatches notifications.
    """

    def __init__(self):
        self.voice_provider = VoiceProvider()
        self.whatsapp_provider = WhatsAppProvider()
        self.email_provider = EmailProvider()
        self.sms_provider = SMSProvider()

    def dispatch_all(
        self,
        transaction: TransactionInput,
        decision: AIDecisionResult
    ) -> List[Dict[str, Any]]:
        """Triggers all four providers for the given transaction."""
        amount = transaction.amount
        cust_id = transaction.customer_id
        phone = "+919876543210"
        email = f"{cust_id.lower()}@customer.com"
        tid = transaction.transaction_id

        results = [
            self.voice_provider.make_call(cust_id, phone, get_template("alert", {"amount": amount, "transaction_id": tid})),
            self.whatsapp_provider.send_message(cust_id, phone, "alert", {"amount": amount, "transaction_id": tid}),
            self.email_provider.send_email(cust_id, email, "Alert", get_template("alert", {"amount": amount, "transaction_id": tid})),
            self.sms_provider.send_sms(cust_id, phone, get_template("alert", {"amount": amount, "transaction_id": tid}))
        ]
        return results

    def dispatch(
        self,
        transaction: Union[TransactionInput, Dict[str, Any]],
        decision: AIDecisionResult,
        policy_allowed: bool
    ) -> List[Dict[str, Any]]:
        if not isinstance(transaction, TransactionInput):
            transaction = preprocess_transaction(transaction)

        action = decision.action
        amount = transaction.amount
        status = transaction.payment_status
        cust_id = transaction.customer_id
        phone = "+919876543210"
        email = f"{cust_id.lower()}@customer.com"

        dispatches = []

        if not policy_allowed:
            # Policy blocked -> optional notification or silent
            return dispatches

        if action == "reminder" or status == "abandoned":
            # WhatsApp + Email
            wa_res = self.whatsapp_provider.send_message(
                cust_id, phone, "abandoned_checkout", {"amount": amount, "transaction_id": transaction.transaction_id}
            )
            email_res = self.email_provider.send_email(
                cust_id, email, "RecoverAI — Complete your purchase", get_template("abandoned_checkout", {"amount": amount, "transaction_id": transaction.transaction_id})
            )
            dispatches.extend([wa_res, email_res])

        elif action == "retry":
            if amount >= 5000:
                # High Value: Voice + WhatsApp
                v_res = self.voice_provider.make_call(
                    cust_id, phone, get_template("payment_retry", {"amount": amount, "transaction_id": transaction.transaction_id})
                )
                wa_res = self.whatsapp_provider.send_message(
                    cust_id, phone, "payment_retry", {"amount": amount, "transaction_id": transaction.transaction_id}
                )
                dispatches.extend([v_res, wa_res])
            else:
                # Standard: WhatsApp + SMS
                wa_res = self.whatsapp_provider.send_message(
                    cust_id, phone, "payment_retry", {"amount": amount, "transaction_id": transaction.transaction_id}
                )
                sms_res = self.sms_provider.send_sms(
                    cust_id, phone, get_template("payment_retry", {"amount": amount, "transaction_id": transaction.transaction_id})
                )
                dispatches.extend([wa_res, sms_res])

        elif action == "escalate":
            email_res = self.email_provider.send_email(
                cust_id, email, "RecoverAI — Action Required on Payment", get_template("escalation", {"amount": amount, "transaction_id": transaction.transaction_id})
            )
            dispatches.append(email_res)

        return dispatches


def orchestrate_communications(
    transaction: Union[TransactionInput, Dict[str, Any]],
    decision: AIDecisionResult,
    policy_allowed: bool
) -> List[Dict[str, Any]]:
    orchestrator = CommunicationOrchestrator()
    return orchestrator.dispatch(transaction, decision, policy_allowed)
