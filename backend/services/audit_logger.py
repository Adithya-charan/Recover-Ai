import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

AUDIT_CSV = Path(__file__).resolve().parents[2] / "data" / "audit_log.csv"

AUDIT_COLUMNS = [
    "transaction_id",
    "customer_id",
    "case_type",
    "amount",
    "payment_status",
    "failure_reason",
    "risk_score",
    "risk_level",
    "agent_diagnosis",
    "agent_action",
    "agent_confidence",
    "agent_reason",
    "policy_decision",
    "policy_reason",
    "execution_status",
    "recovery_status",
    "recovered_amount",
    "execution_message",
    "communication_attempts",
    "communication_channel",
    "provider",
    "provider_reference",
    "executed_at",
]


class AuditLogger:
    """
    Audit logging service for RecoverAI.

    Every live recovery execution appends a record to data/audit_log.csv so
    the full history survives process restarts.  An in-memory list is also
    maintained for the current process lifetime (used by the API layer).
    """

    def __init__(self):
        self._in_memory_logs: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_event(
        self,
        transaction_id: str,
        customer_id: str,
        amount: float,
        payment_status: str,
        failure_reason: str,
        risk_score: int,
        risk_level: str,
        agent_diagnosis: str,
        agent_action: str,
        agent_confidence: float,
        agent_reason: str,
        policy_decision: str,
        policy_reason: str,
        execution_status: str,
        recovery_status: str,
        recovered_amount: float,
        execution_message: str,
        executed_at: Optional[str] = None,
        case_type: str = "",
        communication_attempts: int = 0,
        communication_channel: str = "",
        provider: str = "",
        provider_reference: str = "",
    ) -> Dict[str, Any]:
        event: Dict[str, Any] = {
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "case_type": case_type,
            "amount": amount,
            "payment_status": payment_status,
            "failure_reason": failure_reason,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "agent_diagnosis": agent_diagnosis,
            "agent_action": agent_action,
            "agent_confidence": agent_confidence,
            "agent_reason": agent_reason,
            "policy_decision": policy_decision,
            "policy_reason": policy_reason,
            "execution_status": execution_status,
            "recovery_status": recovery_status,
            "recovered_amount": recovered_amount,
            "execution_message": execution_message,
            "communication_attempts": communication_attempts,
            "communication_channel": communication_channel,
            "provider": provider,
            "provider_reference": provider_reference,
            "executed_at": executed_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._in_memory_logs.append(event)
        self._persist(event)
        return event

    def get_logs(self) -> List[Dict[str, Any]]:
        return list(self._in_memory_logs)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _persist(self, event: Dict[str, Any]) -> None:
        """Append a single audit event to data/audit_log.csv.

        Backward compatible: existing rows without the new provider/communication
        columns will be read fine — missing cells default to empty string.
        New rows always write all columns.
        """
        try:
            AUDIT_CSV.parent.mkdir(parents=True, exist_ok=True)
            file_exists = AUDIT_CSV.exists() and os.path.getsize(AUDIT_CSV) > 0
            with open(AUDIT_CSV, "a", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(
                    fh,
                    fieldnames=AUDIT_COLUMNS,
                    extrasaction="ignore",
                    restval="",          # fills missing keys with empty string
                )
                if not file_exists:
                    writer.writeheader()
                writer.writerow(event)
        except Exception as exc:
            # Audit persistence must never crash the recovery pipeline.
            print(f"[AuditLogger] WARNING: Failed to persist audit event: {exc}")


# ---------------------------------------------------------------------------
# Batch helper — called by the data pipeline scripts
# ---------------------------------------------------------------------------

def generate_audit_log(input_file: str, output_file: str) -> pd.DataFrame:
    dataframe = pd.read_csv(input_file)
    cols = [c for c in AUDIT_COLUMNS if c in dataframe.columns]
    audit_log = dataframe[cols].copy()
    audit_log.to_csv(output_file, index=False)
    return audit_log


if __name__ == "__main__":
    generate_audit_log("data/execution_results.csv", "data/audit_log.csv")
    print("Audit log generated.")
