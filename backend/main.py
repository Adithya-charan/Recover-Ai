import os
import math
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas.transaction import TransactionInput
from backend.schemas.recovery import PipelineResult
from backend.schemas.case import RecoveryCaseInput
from backend.services.preprocessing import preprocess_transaction
from backend.services.recovery_pipeline import process_transaction
from backend.services.recovery_orchestrator import process_orchestrated_recovery
from backend.services.case_manager import get_case_manager
from backend.services.case_orchestrator import process_orchestrated_case
from backend.ml.inference import predict_recovery_ml
from backend.llm.model_adapter import decide_recovery_llm
from backend.payment.provider import get_payment_provider, execute_payment_recovery
from backend.communications.orchestrator import orchestrate_communications
from backend.services.razorpay_service import RazorpayService


app = FastAPI(
    title="RecoverAI",
    description="AI Revenue Recovery & Revenue Intelligence Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

_in_memory_communications: List[Dict[str, Any]] = []
_in_memory_payments: List[Dict[str, Any]] = []


def _clean_value(v):
    if pd.isna(v):
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, bool) or isinstance(v, np.bool_):
        return bool(v)
    return v


def _safe_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    records = df.to_dict(orient="records")
    return [{k: _clean_value(v) for k, v in row.items()} for row in records]


def _load_csv(filename: str, required: Optional[List[str]] = None) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found")
    df = pd.read_csv(path)
    if required:
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise HTTPException(
                status_code=500,
                detail=f"Missing columns in {filename}: {', '.join(missing)}",
            )
    return df


def _load_transactions() -> pd.DataFrame:
    return _load_csv("transactions.csv", ["payment_status", "recovery_eligible", "amount"])


def _load_execution() -> pd.DataFrame:
    try:
        return _load_csv("execution_results.csv", ["execution_status", "recovery_status", "amount"])
    except HTTPException as exc:
        if exc.status_code == 404:
            return pd.DataFrame()
        raise


def _execution_stats(execution: pd.DataFrame) -> Dict[str, Any]:
    recovery_attempts = 0
    blocked_actions = 0
    recovered_amount = 0.0
    successful_recoveries = 0

    if not execution.empty:
        if "execution_status" in execution.columns:
            recovery_attempts = int((execution["execution_status"].isin(["EXECUTED", "SIMULATED"])).sum())
            blocked_actions = int((execution["execution_status"] == "BLOCKED").sum())
        if "recovery_status" in execution.columns:
            recovered_rows = execution[execution["recovery_status"] == "RECOVERED"]
            successful_recoveries = len(recovered_rows)
            if "recovered_amount" in recovered_rows.columns:
                recovered_amount = float(recovered_rows["recovered_amount"].sum() or 0)
            elif "amount" in recovered_rows.columns:
                recovered_amount = float(recovered_rows["amount"].sum() or 0)

    return {
        "recovery_attempts": recovery_attempts,
        "blocked_actions": blocked_actions,
        "recovered_amount": recovered_amount,
        "successful_recoveries": successful_recoveries,
    }


# ==========================================
# EXISTING CORE GET ENDPOINTS
# ==========================================

@app.get("/")
def root():
    return {
        "project": "RecoverAI",
        "status": "running",
        "version": "1.0.0",
        "mode": os.environ.get("RECOVERY_MODE", "simulation"),
        "llm_provider": os.environ.get("LLM_PROVIDER", "simulation")
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/razorpay/test")
def razorpay_test():
    try:
        svc = RazorpayService()
        orders = svc.get_orders(count=5)
        return {"connected": True, "orders": orders}
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@app.get("/api/dashboard")
def dashboard():
    """
    Dashboard KPIs sourced from historical pipeline data (transactions.csv + execution_results.csv).
    Recovery case metrics from live orchestrations are at /api/recovery/metrics.
    """
    transactions = _load_transactions()
    failed = transactions[transactions["payment_status"].isin(["failed", "abandoned"])]
    recovery_eligible = transactions[transactions["recovery_eligible"] == True]
    revenue_at_risk = float(recovery_eligible["amount"].sum() or 0)

    execution = _load_execution()
    stats = _execution_stats(execution)

    return {
        "data_source": "historical_pipeline_csv",
        "total_transactions": len(transactions),
        "failed_transactions": len(failed),
        "recovery_eligible": len(recovery_eligible),
        "revenue_at_risk": revenue_at_risk,
        "recovered_amount": stats["recovered_amount"],
        "recovery_attempts": stats["recovery_attempts"],
        "successful_recoveries": stats["successful_recoveries"],
        "blocked_actions": stats["blocked_actions"],
    }


@app.get("/api/metrics")
def metrics():
    """
    Performance metrics from historical pipeline data (transactions.csv + execution_results.csv).
    For live recovery metrics use /api/recovery/metrics.
    """
    transactions = _load_transactions()
    recovery_eligible = transactions[transactions["recovery_eligible"] == True]
    revenue_at_risk = float(recovery_eligible["amount"].sum() or 0)

    execution = _load_execution()
    stats = _execution_stats(execution)

    n_eligible = len(recovery_eligible)
    r_attempts = stats["recovery_attempts"]
    r_successes = stats["successful_recoveries"]
    r_amount = stats["recovered_amount"]

    recovery_rate = round(r_successes / n_eligible * 100, 2) if n_eligible > 0 else 0
    attempt_success_rate = round(r_successes / r_attempts * 100, 2) if r_attempts > 0 else 0
    revenue_recovery_rate = round(r_amount / revenue_at_risk * 100, 2) if revenue_at_risk > 0 else 0

    return {
        "total_transactions": len(transactions),
        "failed_transactions": len(
            transactions[transactions["payment_status"].isin(["failed", "abandoned"])]
        ),
        "recovery_eligible": n_eligible,
        "revenue_at_risk": revenue_at_risk,
        "recovered_amount": r_amount,
        "recovery_attempts": r_attempts,
        "successful_recoveries": r_successes,
        "blocked_actions": stats["blocked_actions"],
        "recovery_rate": recovery_rate,
        "attempt_success_rate": attempt_success_rate,
        "revenue_recovery_rate": revenue_recovery_rate,
    }


@app.get("/api/transactions")
def get_transactions_endpoint():
    data = _load_transactions()
    return {"count": len(data), "items": _safe_records(data)}


@app.get("/api/decisions")
def decisions():
    data = _load_csv("recovery_decisions.csv")
    return {"count": len(data), "items": _safe_records(data)}


@app.get("/api/execution")
def execution():
    data = _load_csv("execution_results.csv")
    return {"count": len(data), "items": _safe_records(data)}


@app.get("/api/audit")
def audit():
    data = _load_csv("audit_log.csv")
    return {"count": len(data), "items": _safe_records(data)}


@app.get("/api/risk")
def risk():
    data = _load_csv("risk_analysis.csv")
    return {"count": len(data), "items": _safe_records(data)}


@app.post("/api/recovery/predict", response_model=PipelineResult)
def predict_recovery(transaction: TransactionInput):
    try:
        result = process_transaction(transaction)
        return result
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Pipeline inference failed: {str(err)}")


@app.post("/api/recovery/evaluate")
def evaluate_recovery():
    try:
        df = _load_transactions()
        results = []
        for _, row in df.iterrows():
            tx_data = row.to_dict()
            res = process_transaction(tx_data)
            results.append(res)

        total_tx = len(results)
        failed_tx = sum(1 for r in results if r.transaction.payment_status in ["failed", "abandoned"])
        eligible_tx = sum(1 for r in results if r.eligibility.eligible)
        attempted_tx = sum(1 for r in results if r.execution.execution_status in ["SIMULATED", "EXECUTED"])
        successful_recoveries = sum(1 for r in results if r.execution.recovery_status == "RECOVERED")
        blocked_tx = sum(1 for r in results if r.policy.policy_status == "blocked")
        revenue_at_risk = float(sum(r.transaction.amount for r in results if r.eligibility.eligible))
        recovered_revenue = float(sum(r.execution.recovered_amount for r in results if r.execution.recovery_status == "RECOVERED"))

        recovery_rate = round(successful_recoveries / eligible_tx * 100, 2) if eligible_tx > 0 else 0
        attempt_success = round(successful_recoveries / attempted_tx * 100, 2) if attempted_tx > 0 else 0
        revenue_recovery = round(recovered_revenue / revenue_at_risk * 100, 2) if revenue_at_risk > 0 else 0

        return {
            "total_transactions": total_tx,
            "failed_transactions": failed_tx,
            "eligible_transactions": eligible_tx,
            "attempted_transactions": attempted_tx,
            "successful_recoveries": successful_recoveries,
            "blocked_transactions": blocked_tx,
            "revenue_at_risk": revenue_at_risk,
            "recovered_revenue": recovered_revenue,
            "recovery_rate": recovery_rate,
            "attempt_success": attempt_success,
            "revenue_recovery": revenue_recovery,
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Dataset evaluation failed: {str(err)}")


# ==========================================
# NEW ADVANCED ENDPOINTS (PHASE 27)
# ==========================================

@app.post("/api/ml/predict")
def ml_predict(transaction: TransactionInput):
    return predict_recovery_ml(transaction)


@app.post("/api/llm/decision")
def llm_decision(transaction: TransactionInput):
    return decide_recovery_llm(transaction)


@app.post("/api/payment/create")
def payment_create(body: Dict[str, Any] = Body(...)):
    provider = get_payment_provider()
    order = provider.create_payment(
        body.get("transaction_id", "TX_NEW"),
        float(body.get("amount", 1000.0)),
        body.get("customer_id", "CUST_NEW")
    )
    _in_memory_payments.append(order)
    return order


@app.post("/api/payment/retry")
def payment_retry(body: Dict[str, Any] = Body(...)):
    tx_id = body.get("transaction_id", "TX_NEW")
    amount = float(body.get("amount", 1000.0))
    res = execute_payment_recovery(tx_id, amount)
    _in_memory_payments.append(res)
    return res


@app.get("/api/payment/status/{transaction_id}")
def payment_status(transaction_id: str):
    provider = get_payment_provider()
    return provider.get_payment_status(transaction_id)


@app.post("/api/payment/webhook")
def payment_webhook(body: Dict[str, Any] = Body(...)):
    provider = get_payment_provider()
    return provider.handle_webhook(body)


@app.post("/api/communication/send")
def comm_send(body: Dict[str, Any] = Body(...)):
    tx = preprocess_transaction(body.get("transaction", {}))
    dec = decide_recovery_llm(tx)
    res = orchestrate_communications(tx, dec, policy_allowed=True)
    _in_memory_communications.extend(res)
    return {"dispatches": res}


@app.post("/api/recovery/execute")
def recovery_execute(transaction: TransactionInput):
    res = process_orchestrated_recovery(transaction)
    if res.get("communications"):
        _in_memory_communications.extend(res["communications"])
    if res.get("payment_result"):
        _in_memory_payments.append(res["payment_result"])
    return res


# ==========================================
# UNIFIED RECOVERY CASE ENDPOINTS (PHASE 28)
# These MUST be defined BEFORE /api/recovery/{transaction_id}
# so FastAPI matches the specific paths first.
# ==========================================

@app.get("/api/recovery/cases")
def get_recovery_cases(case_type: Optional[str] = None, status: Optional[str] = None):
    mgr = get_case_manager()
    items = mgr.get_all_cases(case_type=case_type, status=status)
    return {"count": len(items), "items": items}


@app.get("/api/recovery/batch-metrics")
def get_recovery_batch_metrics():
    mgr = get_case_manager()
    return mgr.calculate_batch_metrics()


@app.get("/api/recovery/metrics")
def get_recovery_metrics():
    """
    Authoritative live recovery metrics sourced from recovery_cases.json.
    Use this endpoint for RecoverAI recovery KPIs (revenue at risk, recovered amount, etc.).
    Distinct from /api/metrics which reads historical execution_results.csv pipeline data.
    """
    mgr = get_case_manager()
    batch = mgr.calculate_batch_metrics()
    return {
        "data_source": "recovery_cases_live",
        "total_cases": batch["total_cases"],
        "total_revenue_at_risk": batch["total_revenue_at_risk"],
        "total_eligible_cases": batch["total_eligible_cases"],
        "total_recovery_attempts": batch["total_recovery_attempts"],
        "total_successful_recoveries": batch["total_successful_recoveries"],
        "total_recovered_amount": batch["total_recovered_amount"],
        "overall_recovery_rate": batch["overall_recovery_rate"],
        "total_blocked_actions": batch["total_blocked_actions"],
        "total_escalated_cases": batch["total_escalated_cases"],
        "case_type_breakdown": batch["case_type_breakdown"],
    }


@app.post("/api/recovery/cases/execute")
def execute_recovery_case(case_input: RecoveryCaseInput):
    mgr = get_case_manager()
    try:
        res = mgr.execute_case(case_input)
        if res.get("communications"):
            _in_memory_communications.extend(res["communications"])
        if res.get("execution_result"):
            _in_memory_payments.append(res["execution_result"])
        return res
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@app.get("/api/recovery/cases/{case_id}")
def get_recovery_case_by_id(case_id: str):
    mgr = get_case_manager()
    case = mgr.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Recovery case {case_id} not found")
    return case


@app.post("/api/recovery/cases/{case_id}/evaluate")
def evaluate_recovery_case(case_id: str):
    mgr = get_case_manager()
    try:
        res = mgr.evaluate_case(case_id)
        return res
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@app.get("/api/recovery/cases/{case_id}/audit")
def get_recovery_case_audit(case_id: str):
    data = _load_csv("audit_log.csv")
    records = _safe_records(data)
    case_audits = [r for r in records if r.get("transaction_id") == case_id or r.get("case_id") == case_id]
    return {"count": len(case_audits), "items": case_audits}


# Wildcard route MUST come after the specific /api/recovery/cases routes
@app.get("/api/recovery/{transaction_id}")
def get_recovery_by_id(transaction_id: str):
    tx = TransactionInput(transaction_id=transaction_id, customer_id="CUST_SEARCH", amount=1999)
    return process_orchestrated_recovery(tx)


@app.get("/api/communications")
def get_communications():
    return {"count": len(_in_memory_communications), "items": _in_memory_communications}


@app.get("/api/payment-events")
def get_payment_events():
    return {"count": len(_in_memory_payments), "items": _in_memory_payments}


@app.get("/api/model-info")
def model_info():
    return {
        "ml_model_version": "ml-v1",
        "llm_provider": os.environ.get("LLM_PROVIDER", "simulation"),
        "recovery_mode": os.environ.get("RECOVERY_MODE", "simulation"),
        "capabilities": ["risk_score", "expected_recovery_value", "recovery_probability", "llm_diagnosis", "policy_governance", "payment_sandbox", "multi_channel_comms", "unified_6_case_scenarios"]
    }

