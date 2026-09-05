import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from backend.schemas.case import RecoveryCaseInput, RecoveryCaseResult, BatchMetricsResult, CaseTypeMetrics
from backend.services.case_orchestrator import process_orchestrated_case

SEED_FILE = Path(__file__).parent.parent / "data" / "recovery_cases.json"


class RecoveryCaseManager:
    """
    Manages persistence, querying, evaluation, execution, and batch metrics for Recovery Cases.
    """

    def __init__(self):
        self._cases: List[Dict[str, Any]] = []
        self.load_cases()

    def load_cases(self) -> List[Dict[str, Any]]:
        if SEED_FILE.exists():
            try:
                with open(SEED_FILE, "r") as f:
                    self._cases = json.load(f)
            except Exception:
                self._cases = []
        return self._cases

    def save_cases(self):
        SEED_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SEED_FILE, "w") as f:
            json.dump(self._cases, f, indent=2)

    def get_all_cases(self, case_type: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self._cases
        if case_type:
            ct = case_type.upper()
            results = [c for c in results if str(c.get("case_type")).upper() == ct]
        if status:
            st = status.lower()
            results = [c for c in results if str(c.get("status")).lower() == st]
        return results

    def get_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        for c in self._cases:
            if c.get("case_id") == case_id or c.get("transaction_id") == case_id:
                return c
        return None

    def create_or_update_case(self, case_input: Union[RecoveryCaseInput, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(case_input, dict):
            c_dict = case_input
        else:
            c_dict = case_input.dict()

        cid = c_dict.get("case_id") or f"CASE_{c_dict.get('case_type', 'PF')[:2]}_{len(self._cases)+101}"
        c_dict["case_id"] = cid

        # Find existing
        existing_idx = None
        for idx, c in enumerate(self._cases):
            if c.get("case_id") == cid:
                existing_idx = idx
                break

        if existing_idx is not None:
            self._cases[existing_idx].update(c_dict)
            res = self._cases[existing_idx]
        else:
            self._cases.append(c_dict)
            res = c_dict

        self.save_cases()
        return res

    def evaluate_case(self, case_id: str) -> Dict[str, Any]:
        case = self.get_case_by_id(case_id)
        if not case:
            raise ValueError(f"Case with id {case_id} not found.")

        result = process_orchestrated_case(case)
        case_res = result["case_result"]
        self.create_or_update_case(case_res)
        return result

    def execute_case(self, case_input: Union[RecoveryCaseInput, Dict[str, Any]]) -> Dict[str, Any]:
        result = process_orchestrated_case(case_input)
        case_res = result["case_result"]
        self.create_or_update_case(case_res)
        return result

    def calculate_batch_metrics(self) -> Dict[str, Any]:
        cases = self.get_all_cases()
        if not cases:
            return {
                "total_cases": 0,
                "total_revenue_at_risk": 0.0,
                "total_eligible_cases": 0,
                "total_recovery_attempts": 0,
                "total_successful_recoveries": 0,
                "total_recovered_amount": 0.0,
                "overall_recovery_rate": 0.0,
                "total_blocked_actions": 0,
                "total_escalated_cases": 0,
                "case_type_breakdown": []
            }

        case_types = ["PAYMENT_FAILURE", "CHECKOUT_ABANDONMENT", "FAILED_SUBSCRIPTION", "B2B_RECEIVABLE", "MANDATE_FAILURE", "PROMISE_TO_PAY"]
        breakdown = []

        total_cases = len(cases)
        total_risk = sum(float(c.get("revenue_at_risk", c.get("amount", 0))) for c in cases)
        total_eligible = sum(1 for c in cases if c.get("status") in ["eligible", "completed", "active"] or c.get("policy_decision") == "ALLOW")
        total_attempts = sum(1 for c in cases if c.get("execution_status") in ["SIMULATED", "EXECUTED"] or c.get("attempt_count", 0) > 0)
        total_successes = sum(1 for c in cases if str(c.get("outcome")).upper() == "RECOVERED")
        total_recovered_amt = sum(float(c.get("recovered_amount", 0)) for c in cases if str(c.get("outcome")).upper() == "RECOVERED")
        total_blocked = sum(1 for c in cases if str(c.get("policy_decision")).upper() == "BLOCK" or c.get("execution_status") == "BLOCKED")
        total_escalated = sum(1 for c in cases if "escalated" in str(c.get("escalation_status")).lower() or str(c.get("outcome")).lower() == "escalated")

        for ct in case_types:
            ct_cases = [c for c in cases if str(c.get("case_type")).upper() == ct]
            ct_count = len(ct_cases)
            if ct_count == 0:
                continue

            ct_risk = sum(float(c.get("revenue_at_risk", c.get("amount", 0))) for c in ct_cases)
            ct_eligible = sum(1 for c in ct_cases if c.get("status") in ["eligible", "completed", "active"] or c.get("policy_decision") == "ALLOW")
            ct_attempts = sum(1 for c in ct_cases if c.get("execution_status") in ["SIMULATED", "EXECUTED"] or c.get("attempt_count", 0) > 0)
            ct_successes = sum(1 for c in ct_cases if str(c.get("outcome")).upper() == "RECOVERED")
            ct_recovered = sum(float(c.get("recovered_amount", 0)) for c in ct_cases if str(c.get("outcome")).upper() == "RECOVERED")
            ct_blocked = sum(1 for c in ct_cases if str(c.get("policy_decision")).upper() == "BLOCK" or c.get("execution_status") == "BLOCKED")
            ct_escalated = sum(1 for c in ct_cases if "escalated" in str(c.get("escalation_status")).lower() or str(c.get("outcome")).lower() == "escalated")
            ct_failed = ct_count - ct_successes

            ct_rate = round((ct_successes / ct_eligible * 100), 2) if ct_eligible > 0 else 0.0

            breakdown.append({
                "case_type": ct,
                "total_cases": ct_count,
                "revenue_at_risk": ct_risk,
                "eligible_cases": ct_eligible,
                "recovery_attempts": ct_attempts,
                "successful_recoveries": ct_successes,
                "recovered_amount": ct_recovered,
                "recovery_rate": ct_rate,
                "blocked_actions": ct_blocked,
                "escalated_cases": ct_escalated,
                "failed_recovery_cases": ct_failed
            })

        overall_rate = round((total_successes / total_eligible * 100), 2) if total_eligible > 0 else 0.0

        return {
            "total_cases": total_cases,
            "total_revenue_at_risk": total_risk,
            "total_eligible_cases": total_eligible,
            "total_recovery_attempts": total_attempts,
            "total_successful_recoveries": total_successes,
            "total_recovered_amount": total_recovered_amt,
            "overall_recovery_rate": overall_rate,
            "total_blocked_actions": total_blocked,
            "total_escalated_cases": total_escalated,
            "case_type_breakdown": breakdown
        }


_case_manager_instance: Optional[RecoveryCaseManager] = None


def get_case_manager() -> RecoveryCaseManager:
    global _case_manager_instance
    if _case_manager_instance is None:
        _case_manager_instance = RecoveryCaseManager()
    return _case_manager_instance
