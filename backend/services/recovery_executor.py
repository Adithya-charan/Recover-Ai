import os
from typing import Union, Dict, Any, Optional
import pandas as pd
from datetime import datetime
from backend.schemas.transaction import TransactionInput
from backend.schemas.decision import AIDecisionResult
from backend.schemas.policy import PolicyResult
from backend.schemas.execution import ExecutionResult
from backend.services.preprocessing import preprocess_transaction
from backend.services.recovery_agent import RecoveryAgent
from backend.services.policy_engine import PolicyEngine


class RecoveryExecutor:
    """
    Simulates recovery execution in safe Test Mode.
    Guarantees no real financial gateway transactions occur.
    """

    def __init__(self, mode: str = "simulation"):
        self.mode = os.environ.get("RECOVERY_MODE", mode).lower()

    def execute(
        self,
        transaction: Union[TransactionInput, Dict[str, Any]],
        decision: Optional[AIDecisionResult] = None,
        policy: Optional[PolicyResult] = None
    ) -> ExecutionResult:
        if not isinstance(transaction, TransactionInput):
            transaction = preprocess_transaction(transaction)

        if decision is None:
            decision = RecoveryAgent().analyze(transaction)

        if policy is None:
            policy = PolicyEngine().evaluate(transaction, decision=decision)

        # Never execute blocked actions.
        if not policy.allowed:
            return ExecutionResult(
                execution_status="BLOCKED",
                recovery_status="not_attempted",
                recovered_amount=0.0,
                execution_message="Recovery action blocked by policy governance."
            )

        action = decision.action

        # Simulation Mode execution logic
        if action == "retry":
            # Deterministic simulation based on transaction_id / amount
            success_probability = 0.75
            deterministic_value = (hash(transaction.transaction_id) % 100) / 100.0

            if deterministic_value < success_probability:
                return ExecutionResult(
                    execution_status="SIMULATED",
                    recovery_status="RECOVERED",
                    recovered_amount=transaction.amount,
                    execution_message="Payment retry succeeded in Test Mode simulation."
                )

            return ExecutionResult(
                execution_status="SIMULATED",
                recovery_status="FAILED",
                recovered_amount=0.0,
                execution_message="Payment retry attempted but failed in Test Mode simulation."
            )

        if action == "reminder":
            return ExecutionResult(
                execution_status="SIMULATED",
                recovery_status="FOLLOW_UP",
                recovered_amount=0.0,
                execution_message="Recovery reminder scheduled in Test Mode simulation."
            )

        return ExecutionResult(
            execution_status="NOT_EXECUTED",
            recovery_status="not_attempted",
            recovered_amount=0.0,
            execution_message=f"Action '{action}' is non-executable."
        )


def execute_action(
    transaction: Union[TransactionInput, Dict[str, Any]],
    decision: Optional[AIDecisionResult] = None,
    policy: Optional[PolicyResult] = None
) -> ExecutionResult:
    executor = RecoveryExecutor()
    return executor.execute(transaction, decision, policy)


def execute_recovery(input_file, output_file):
    dataframe = pd.read_csv(input_file)
    executor = RecoveryExecutor()

    results = []
    for _, row in dataframe.iterrows():
        tx = preprocess_transaction(row.to_dict())
        res = executor.execute(tx)
        results.append(res)

    dataframe["execution_status"] = [r.execution_status for r in results]
    dataframe["recovery_status"] = [r.recovery_status for r in results]
    dataframe["recovered_amount"] = [r.recovered_amount for r in results]
    dataframe["execution_message"] = [r.execution_message for r in results]
    dataframe["executed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    dataframe.to_csv(output_file, index=False)
    return dataframe


if __name__ == "__main__":
    execute_recovery("data/policy_decisions.csv", "data/execution_results.csv")
    print("Recovery execution simulation completed.")