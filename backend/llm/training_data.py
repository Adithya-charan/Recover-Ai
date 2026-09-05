import json
from pathlib import Path
import pandas as pd
from backend.llm.prompts import SYSTEM_RECOVERY_PROMPT, build_user_prompt

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LLM_DATA_DIR = DATA_DIR / "llm"


def prepare_training_dataset(
    transactions_csv: str = "transactions.csv",
    output_jsonl: str = "train.jsonl"
) -> str:
    """
    Converts RecoverAI transaction records into instruction-tuning JSONL format for LoRA fine-tuning.
    Note: Labels ('assistant' recommendations) are derived from RecoveryAgent rules (synthetic labels).
    """
    LLM_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = LLM_DATA_DIR / output_jsonl

    tx_path = DATA_DIR / transactions_csv
    if not tx_path.exists():
        raise FileNotFoundError(f"{transactions_csv} not found in {DATA_DIR}")

    df = pd.read_csv(tx_path)

    # Load decisions if available for diagnosis/reason
    dec_path = DATA_DIR / "recovery_decisions.csv"
    if dec_path.exists():
        dec_df = pd.read_csv(dec_path)
        merged = pd.merge(df, dec_df[["transaction_id", "agent_diagnosis", "agent_action", "agent_confidence", "agent_reason"]], on="transaction_id", how="left")
    else:
        merged = df

    records = []
    for _, row in merged.iterrows():
        tx_data = {
            "transaction_id": row.get("transaction_id", "TX_0"),
            "customer_id": row.get("customer_id", "CUST_0"),
            "amount": row.get("amount", 0),
            "payment_status": row.get("payment_status", "failed"),
            "failure_reason": row.get("failure_reason", "unknown"),
            "attempt_count": row.get("attempt_count", 1),
            "customer_previous_payments": row.get("customer_previous_payments", 0),
            "customer_previous_failures": row.get("customer_previous_failures", 0),
            "days_since_event": row.get("days_since_event", 0),
            "subscription_status": row.get("subscription_status", "not_applicable")
        }

        eligibility_data = {
            "eligible": bool(row.get("recovery_eligible", False)),
            "reason": "Criteria evaluated based on transaction state."
        }

        risk_data = {
            "risk_score": int(row.get("risk_score", 40)) if "risk_score" in row and not pd.isna(row["risk_score"]) else 40,
            "risk_level": str(row.get("risk_level", "medium")) if "risk_level" in row and not pd.isna(row["risk_level"]) else "medium"
        }

        action = str(row.get("agent_action") or row.get("recommended_action") or "stop").lower()
        if action not in {"retry", "reminder", "escalate", "stop"}:
            action = "stop"

        diagnosis = str(row.get("agent_diagnosis") or "Payment recovery assessment.")
        reason = str(row.get("agent_reason") or "Rule-based recommendation.")
        confidence = float(row.get("agent_confidence", 0.85)) if "agent_confidence" in row and not pd.isna(row["agent_confidence"]) else 0.85

        user_content = build_user_prompt(tx_data, eligibility_data, risk_data)
        assistant_content = json.dumps({
            "action": action,
            "diagnosis": diagnosis,
            "reason": reason,
            "confidence": round(confidence, 2)
        })

        example = {
            "system": SYSTEM_RECOVERY_PROMPT.strip(),
            "user": user_content.strip(),
            "assistant": assistant_content
        }

        records.append(example)

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[RecoverAI LLM Dataset] Saved {len(records)} instruction examples to {out_path}")
    return str(out_path)


if __name__ == "__main__":
    prepare_training_dataset()
