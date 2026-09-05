from backend.schemas.transaction import TransactionInput
from backend.services.recovery_orchestrator import UnifiedRecoveryOrchestrator

orch = UnifiedRecoveryOrchestrator()
tx = TransactionInput(
    transaction_id="TX_ORCH_01",
    customer_id="C01",
    amount=1999,
    payment_status="failed",
    failure_reason="timeout",
    attempt_count=1,
    days_since_event=2
)
res = orch.process_recovery(tx)
print("llm_decision action:", res["llm_decision"]["action"])
print("policy allowed:", res["pipeline_result"].policy.allowed)
print("policy reason:", res["pipeline_result"].policy.reason)
print("communications count:", len(res["communications"]))
print("payment_result:", res["payment_result"])
