# RecoverAI — AI Revenue Recovery Engine & Policy Governance Platform

**RecoverAI** is an enterprise-grade AI-powered Revenue Recovery & Revenue Intelligence platform. It intelligently analyzes failed and abandoned payment transactions, determines recovery eligibility, evaluates transaction risk with Advanced ML, generates LLM-driven recovery recommendations, enforces strict Policy Governance, executes Sandbox Payment Retries, dispatches Multi-Channel Communications (Voice, WhatsApp, Email, SMS), and logs immutable audit trails.

---

## 🏗️ Target Architecture & End-to-End Pipeline

```
                  React Dashboard
                         │
                         ▼
                     FastAPI
                         │
                         ▼
               Recovery Orchestrator
                         │
                         ▼
                  Preprocessing
                         │
                         ▼
                   Eligibility
                         │
                         ▼
                  Advanced ML Model
                         │
                         ▼
                  Fine-Tuned LLM
                         │
                         ▼
                 Policy Governance
                    │          │
                  BLOCK       ALLOW
                    │          │
                    │          ▼
                    │     Recovery Executor (Payment Sandbox + Multi-Channel Comms)
                    │          │
                    └────┬─────┘
                         ▼
              Audit Logger & DB Persistence
                         │
                         ▼
                  PipelineResult
```

---

## 🚀 Key Modules & Capabilities (Phases 1–36)

- **Data Contracts (`backend/schemas/`)**: Pydantic models ensuring strict data boundary validation.
- **Preprocessing (`backend/services/preprocessing.py`)**: Type casting, NaN/Inf handling, string lowercasing, and dirty value sanitization.
- **Eligibility Engine (`backend/services/eligibility_engine.py`)**: Recovery criteria evaluation.
- **Advanced ML Mode (`backend/ml/`)**: Feature extraction (`features.py`), model inference (`model.py`), predicting `recovery_probability` (0–1.0), `risk_score` (0–100), `risk_level`, and `expected_recovery_value`.
- **Fine-Tuned LLM Agent (`backend/llm/`)**: Configurable adapter (`model_adapter.py`) with support for local/huggingface/hosted LLMs (`LLM_PROVIDER=simulation|huggingface|openai`). Non-bypassable Policy Engine remains the final authorization authority.
- **Policy Governance (`backend/services/policy_engine.py`)**: Enforces hard compliance rules (max retry limit: 2, max recovery amount: ₹10,000, 7-day age window).
- **Payment Gateway Sandbox (`backend/payment/`)**: Sandbox payment adapter supporting order creation, retry simulation (`RECOVERY_MODE=simulation|sandbox`), idempotency, and webhook verification.
- **Multi-Channel Communication Engine (`backend/communications/`)**: Strategy selector dispatching targeted recovery messages via **Voice**, **WhatsApp**, **Email**, and **SMS**.
- **Database Persistence (`backend/database/`)**: SQLite storage (`recoverai.db`) using SQLAlchemy ORM for transactions, predictions, payment events, and audit logs.
- **Unified Orchestrator (`backend/services/recovery_orchestrator.py`)**: Provides `process_orchestrated_recovery()` connecting all modules into one execution flow.

---

## 🛠️ Environment Configuration

Create a `.env` file in the project root:

```ini
RECOVERY_MODE=simulation
LLM_PROVIDER=simulation
LLM_MODEL=recoverai-llm-v1
LLM_API_KEY=
RAZORPAY_KEY_ID=rzp_test_key_id
RAZORPAY_KEY_SECRET=rzp_test_key_secret
```

---

## 🚦 How to Run the Project

### 1. Start FastAPI Backend
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### 2. Start React Frontend
```bash
cd frontend
npm run dev
```

### 3. Build Frontend for Production
```bash
cd frontend
npm run build
```

---

## 🧪 Automated Testing

Run the complete Python test suite:
```bash
python -m unittest discover tests/
```

---

## 🔌 API Endpoints Summary

- `GET /health`: Health check.
- `GET /api/dashboard`: Dashboard card metrics.
- `GET /api/metrics`: Performance recovery rates.
- `GET /api/transactions`: Transaction history.
- `GET /api/decisions`: Decision records.
- `GET /api/execution`: Execution records.
- `GET /api/audit`: Audit trail history.
- `GET /api/risk`: Risk analysis records.
- `POST /api/recovery/predict`: Standard pipeline prediction.
- `POST /api/recovery/evaluate`: Batch dataset evaluation.
- `POST /api/ml/predict`: Advanced ML inference.
- `POST /api/llm/decision`: Fine-Tuned LLM agent recommendation.
- `POST /api/payment/create`: Sandbox payment order creation.
- `POST /api/payment/retry`: Sandbox payment retry attempt.
- `POST /api/communication/send`: Multi-channel communication dispatch.
- `POST /api/recovery/execute`: Full unified orchestrated recovery pipeline execution.
- `GET /api/model-info`: Active model versions & provider status.
