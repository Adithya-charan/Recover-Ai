import os, sys, json
# Ensure project root is in PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

os.environ['HF_HOME'] = r'F:/Razorpay/.hf_cache'

from backend.services.recovery_pipeline import process_transaction
from backend.communications.orchestrator import CommunicationOrchestrator

# Sample transaction matching TransactionInput schema
sample_tx = {
    "transaction_id": "tx_001",
    "customer_id": "cust_001",
    "amount": 6000,
    "payment_status": "failed",
    "failure_reason": "network_error",
    "attempt_count": 1,
    "customer_previous_payments": 3,
    "customer_previous_failures": 0,
    "days_since_event": 2,
    "payment_method": "card",
    "currency": "INR"
}

# Run full pipeline
pipeline_result = process_transaction(sample_tx)
print("=== Pipeline Result ===")
print(json.dumps(pipeline_result.dict(), indent=2))

# Unified communication using dispatch_all (simultaneous channels)
orchestrator = CommunicationOrchestrator()
all_dispatches = orchestrator.dispatch_all(pipeline_result.transaction, pipeline_result.decision, pipeline_result.policy.allowed)
print("=== All Dispatches (Voice, WhatsApp, Email, SMS) ===")
print(json.dumps(all_dispatches, indent=2))
