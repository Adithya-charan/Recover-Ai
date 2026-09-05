from typing import Union, Dict, Any
from backend.schemas.transaction import TransactionInput
from backend.schemas.recovery import EligibilityResult, PipelineResult
from backend.schemas.risk import RiskResult
from backend.schemas.decision import AIDecisionResult
from backend.schemas.policy import PolicyResult
from backend.schemas.execution import ExecutionResult

from backend.services.preprocessing import preprocess_transaction
from backend.services.eligibility_engine import EligibilityEngine
from backend.services.risk_detector import RiskDetector
from backend.services.recovery_agent import RecoveryAgent
from backend.services.policy_engine import PolicyEngine
from backend.services.recovery_executor import RecoveryExecutor
from backend.services.audit_logger import AuditLogger


class RecoveryPipeline:
    """
    Unified Orchestration Layer for RecoverAI.
    Executes the complete connected pipeline:
    Transaction -> Preprocessing -> Eligibility -> Risk -> AI Decision -> Policy Governance -> Recovery Executor -> Audit Logger -> PipelineResult
    """

    def __init__(self):
        self.eligibility_engine = EligibilityEngine()
        self.risk_detector = RiskDetector()
        self.recovery_agent = RecoveryAgent()
        self.policy_engine = PolicyEngine()
        self.recovery_executor = RecoveryExecutor()
        self.audit_logger = AuditLogger()

    def process_transaction(self, raw_transaction: Union[TransactionInput, Dict[str, Any]]) -> PipelineResult:
        # 1. Preprocessing
        tx = preprocess_transaction(raw_transaction)

        # 2. Eligibility Analysis
        eligibility = self.eligibility_engine.evaluate(tx)

        # 3. Risk Analysis
        risk = self.risk_detector.evaluate(tx)

        # 4. AI Decision Engine
        decision = self.recovery_agent.analyze(tx, eligibility=eligibility, risk=risk)

        # 5. Policy Engine
        policy = self.policy_engine.evaluate(tx, decision=decision, eligibility=eligibility, risk=risk)

        # 6. Execution Engine (Simulation Mode)
        execution = self.recovery_executor.execute(tx, decision=decision, policy=policy)

        # 7. Determine Final Status
        if not eligibility.eligible:
            final_status = "stopped"
        elif not policy.allowed:
            final_status = "blocked"
        elif execution.recovery_status == "RECOVERED":
            final_status = "recovered"
        elif execution.recovery_status == "FOLLOW_UP":
            final_status = "follow_up"
        else:
            final_status = "failed"

        # 8. Record Audit Event
        self.audit_logger.record_event(
            transaction_id=tx.transaction_id,
            customer_id=tx.customer_id,
            amount=tx.amount,
            payment_status=tx.payment_status,
            failure_reason=tx.failure_reason,
            risk_score=risk.risk_score,
            risk_level=risk.risk_level,
            agent_diagnosis=decision.diagnosis,
            agent_action=decision.action,
            agent_confidence=decision.confidence,
            agent_reason=decision.reason,
            policy_decision="ALLOW" if policy.allowed else "BLOCK",
            policy_reason=policy.reason,
            execution_status=execution.execution_status,
            recovery_status=execution.recovery_status,
            recovered_amount=execution.recovered_amount,
            execution_message=execution.execution_message
        )

        # 9. Return Unified Pipeline Result
        return PipelineResult(
            transaction_id=tx.transaction_id,
            transaction=tx,
            eligibility=eligibility,
            risk=risk,
            decision=decision,
            policy=policy,
            execution=execution,
            final_status=final_status
        )


def process_transaction(transaction: Union[TransactionInput, Dict[str, Any]]) -> PipelineResult:
    pipeline = RecoveryPipeline()
    return pipeline.process_transaction(transaction)
