from typing import Dict, Any


def get_template(template_name: str, params: Dict[str, Any]) -> str:
    amount = f"₹{params.get('amount', 0):,.2f}"
    tx_id = params.get("transaction_id", "UNKNOWN")

    templates = {
        "payment_retry": f"Your payment of {amount} for order {tx_id} requires attention. Please complete your transaction securely.",
        "abandoned_checkout": f"You left items in your cart! Complete your purchase of {amount} now.",
        "escalation": f"Notice regarding your payment of {amount} ({tx_id}). Please contact support or update payment details.",
        "confirmation": f"Great news! Your payment of {amount} ({tx_id}) has been successfully recovered."
    }

    return templates.get(template_name, f"Payment notification regarding transaction {tx_id} of {amount}.")
