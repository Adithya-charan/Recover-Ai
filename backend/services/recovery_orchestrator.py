from typing import Union, Dict, Any, List
from backend.schemas.transaction import TransactionInput
from backend.schemas.recovery import PipelineResult, EligibilityResult
from backend.schemas.risk import RiskResult
from backend.schemas.decision import AIDecisionResult
from backend.schemas.policy import PolicyResult
from backend.schemas.execution import ExecutionResult

from backend.services.preprocessing import preprocess_transaction
from backend.services.eligibility_engine import EligibilityEngine
from backend.ml.inference import predict_recovery_ml
from backend.llm.model_adapter import LLMDecisionAdapter
from backend.services.policy_engine import PolicyEngine
from backend.payment.provider import execute_payment_recovery
from backend.communications.orchestrator import CommunicationOrchestrator
from backend.services.audit_logger import AuditLogger


class UnifiedRecoveryOrchestrator:
    """
    Unified Recovery Orchestrator connecting:
    Preprocessing -> Eligibility -> Advanced ML -> Fine-Tuned LLM -> Policy Governance -> Payment Sandbox -> Multi-Channel Comms -> Audit Logger
    """

    def __init__(self):
        self.eligibility_engine = EligibilityEngine()
        self.llm_adapter = LLMDecisionAdapter()
        self.policy_engine = PolicyEngine()
        self.communication_orchestrator = CommunicationOrchestrator()
        self.audit_logger = AuditLogger()

    def process_recovery(self, raw_transaction: Union[TransactionInput, Dict[str, Any]]) -> Dict[str, Any]:
        # 1. Preprocessing
        tx = preprocess_transaction(raw_transaction)

        # 2. Eligibility Engine
        eligibility = self.eligibility_engine.evaluate(tx)

        # 3. Advanced ML Model (recovery_probability, risk_score, risk_level, expected_recovery_value)
        ml_res = predict_recovery_ml(tx)
        risk = RiskResult(
            risk_score=ml_res["risk_score"],
            risk_level=ml_res["risk_level"],
            confidence=ml_res["recovery_probability"],
            model_version=ml_res["model_version"],
            detected_revenue_at_risk=ml_res["expected_recovery_value"]
        )

        # 4. Fine-Tuned LLM Decision Agent
        llm_decision = self.llm_adapter.generate_decision(tx, eligibility=eligibility, risk=risk)

        # 5. Policy Engine (Non-bypassable final authority)
        policy = self.policy_engine.evaluate(tx, decision=llm_decision, eligibility=eligibility, risk=risk)

        payment_result = {}
        communications = []

        # 6. Payment & Communication Execution
        if not policy.allowed:
            execution = ExecutionResult(
                execution_status="BLOCKED",
                recovery_status="not_attempted",
                recovered_amount=0.0,
                execution_message=f"Recovery blocked by policy governance: {policy.reason}"
            )
            final_status = "blocked"
        else:
            if llm_decision.action == "retry":
                payment_result = execute_payment_recovery(tx.transaction_id, tx.amount, tx.customer_id)
                recovered_amt = payment_result.get("amount", tx.amount) if payment_result.get("recovered") else 0.0
                rec_status = "RECOVERED" if payment_result.get("recovered") else "FAILED"
                execution = ExecutionResult(
                    execution_status="SIMULATED",
                    recovery_status=rec_status,
                    recovered_amount=recovered_amt,
                    execution_message=payment_result.get("gateway_message", "Payment executed.")
                )
                final_status = "recovered" if payment_result.get("recovered") else "failed"
            elif llm_decision.action == "reminder":
                execution = ExecutionResult(
                    execution_status="SIMULATED",
                    recovery_status="FOLLOW_UP",
                    recovered_amount=0.0,
                    execution_message="Reminder recovery scheduled."
                )
                final_status = "follow_up"
            else:
                execution = ExecutionResult(
                    execution_status="NOT_EXECUTED",
                    recovery_status="not_attempted",
                    recovered_amount=0.0,
                    execution_message=f"Action '{llm_decision.action}' non-executable."
                )
                final_status = "stopped"

            # Multi-Channel Communications
            communications = self.communication_orchestrator.dispatch(tx, llm_decision, policy.allowed)

        # 7. Audit Event Recording
        audit_event = self.audit_logger.record_event(
            transaction_id=tx.transaction_id,
            customer_id=tx.customer_id,
            amount=tx.amount,
            payment_status=tx.payment_status,
            failure_reason=tx.failure_reason,
            risk_score=risk.risk_score,
            risk_level=risk.risk_level,
            agent_diagnosis=llm_decision.diagnosis,
            agent_action=llm_decision.action,
            agent_confidence=llm_decision.confidence,
            agent_reason=llm_decision.reason,
            policy_decision="ALLOW" if policy.allowed else "BLOCK",
            policy_reason=policy.reason,
            execution_status=execution.execution_status,
            recovery_status=execution.recovery_status,
            recovered_amount=execution.recovered_amount,
            execution_message=execution.execution_message,
            case_type="PAYMENT_FAILURE",
            communication_attempts=len(communications),
        )

        pipeline_result = PipelineResult(
            transaction_id=tx.transaction_id,
            transaction=tx,
            eligibility=eligibility,
            risk=risk,
            decision=llm_decision,
            policy=policy,
            execution=execution,
            final_status=final_status
        )

        return {
            "pipeline_result": pipeline_result,
            "ml_insights": ml_res,
            "llm_decision": llm_decision.dict() if hasattr(llm_decision, "dict") else dict(llm_decision),
            "payment_result": payment_result,
            "communications": communications,
            "audit_event": audit_event
        }


def process_orchestrated_recovery(transaction: Union[TransactionInput, Dict[str, Any]]) -> Dict[str, Any]:
    orchestrator = UnifiedRecoveryOrchestrator()
    return orchestrator.process_recovery(transaction)
