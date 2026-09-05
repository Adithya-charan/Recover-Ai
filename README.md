# RecoverAI — AI Revenue Recovery & Revenue Intelligence Platform

**RecoverAI** is an AI-powered Revenue Recovery & Revenue Intelligence platform designed to detect revenue at risk, understand why revenue is slipping away, determine the right recovery intervention, execute bounded recovery actions, communicate with customers, and maintain a complete audit trail.

RecoverAI combines **Advanced ML, a Fine-Tuned LLM, Policy Governance, Razorpay Payment Infrastructure, Multi-Channel Communication, and an AI Recovery Orchestrator** into one unified recovery engine.

---

## 🎯 Hackathon Track

### AI Revenue Recovery — Find revenue that's slipping away and win it back

RecoverAI addresses revenue leakage caused by:

- Failed payments
- Checkout abandonment
- Failed subscriptions
- Overdue B2B receivables
- Mandate failures
- Broken payment promises

The system does not stop at identifying risk. It follows the complete lifecycle:

**Detect → Predict → Diagnose → Recommend → Authorize → Execute → Communicate → Recover → Audit**

The core principle is:

> **AI recommends → Policy authorizes → Executor executes**

This ensures that AI cannot independently perform an unrestricted financial action.

---

## 🚀 What RecoverAI Does

RecoverAI analyzes revenue-risk events and determines the most appropriate recovery strategy. The platform:

1. Detects revenue-risk events
2. Calculates revenue at risk
3. Checks recovery eligibility
4. Predicts recovery probability using ML
5. Calculates transaction risk
6. Uses a fine-tuned LLM for diagnosis and recommendation
7. Applies deterministic policy governance
8. Authorizes or blocks the proposed action
9. Executes bounded recovery workflows
10. Sends customer communications
11. Tracks recovery outcomes
12. Records the complete decision lifecycle
13. Calculates recovery metrics across batches

---

## 🏗️ End-to-End Architecture

```text
                         ┌──────────────────────┐
                         │    React Dashboard    │
                         └──────────┬────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      FastAPI API     │
                         └──────────┬────────────┘
                                    │
                                    ▼
                     ┌────────────────────────────┐
                     │    Recovery Orchestrator   │
                     └──────────────┬─────────────┘
                                    │
                                    ▼
                     ┌────────────────────────────┐
                     │       Preprocessing        │
                     └──────────────┬─────────────┘
                                    │
                                    ▼
                     ┌────────────────────────────┐
                     │      Eligibility Engine    │
                     └──────────────┬─────────────┘
                                    │
                                    ▼
                     ┌────────────────────────────┐
                     │      Advanced ML Model     │
                     │                            │
                     │ • Recovery Probability     │
                     │ • Risk Score               │
                     │ • Risk Level               │
                     │ • Expected Recovery Value  │
                     └──────────────┬─────────────┘
                                    │
                                    ▼
                     ┌────────────────────────────┐
                     │      Fine-Tuned LLM        │
                     │                            │
                     │ • Diagnosis                │
                     │ • Recommendation           │
                     │ • Confidence                │
                     │ • Reasoning                 │
                     └──────────────┬─────────────┘
                                    │
                                    ▼
                     ┌────────────────────────────┐
                     │      Policy Governance     │
                     └──────────────┬─────────────┘
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                       BLOCK                 ALLOW
                         │                     │
                         │                     ▼
                         │          ┌────────────────────┐
                         │          │ Recovery Executor  │
                         │          └─────────┬──────────┘
                         │                    │
                         │          ┌─────────┴─────────┐
                         │          │                   │
                         │          ▼                   ▼
                         │   Payment Recovery     Communications
                         │                              │
                         │                    ┌─────────┼─────────┐
                         │                    ▼          ▼         ▼
                         │                  Voice   WhatsApp   Email / SMS
                         │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                             ┌────────────────────┐
                             │   Outcome Engine   │
                             └─────────┬──────────┘
                                       │
                                       ▼
                             ┌────────────────────┐
                             │    Audit Logger    │
                             └─────────┬──────────┘
                                       │
                                       ▼
                             ┌────────────────────┐
                             │  Recovery Metrics  │
                             └────────────────────┘
```

---

## 🧠 Core Design Philosophy

RecoverAI separates **intelligence, authorization, and execution**.

```text
                    AI Intelligence
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
             ML                    LLM
              │                     │
              └──────────┬──────────┘
                         ▼
                  AI Recommendation
                         │
                         ▼
                Policy Governance
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
            BLOCK                 ALLOW
              │                     │
              │                     ▼
              │              Bounded Executor
              │                     │
              │                     ▼
              │              Recovery Action
              │
              └──────────────► Audit
```

The LLM does **not** directly execute payment actions. Every financial recovery action must pass through policy authorization.

---

## 💰 Revenue Recovery Flows

RecoverAI uses a unified recovery engine supporting six different revenue-loss scenarios.

### 1. Payment Failure

```text
Failed Payment → Detect Revenue at Risk → Eligibility Check → ML Risk Prediction
→ LLM Diagnosis → Recovery Recommendation → Policy Authorization → Payment Retry
→ Customer Communication → Recovery Outcome → Audit
```

The system determines whether a failed payment is suitable for automated recovery.

### 2. Checkout Abandonment

```text
Checkout Started → Customer Abandons Checkout → Revenue at Risk → Eligibility
→ ML Risk Assessment → LLM Recommendation → Policy Authorization
→ Follow-Up / Reminder → Outcome → Audit
```

Checkout abandonment does not trigger an unauthorized payment retry — the recovery action is designed around customer follow-up.

### 3. Failed Subscription

```text
Subscription Payment Failure → Revenue at Risk → Eligibility → ML Risk Prediction
→ LLM Diagnosis → Dunning Recommendation → Policy Authorization → Bounded Retry
→ Communication → Outcome → Audit
```

This flow supports subscription recovery through controlled retry and communication actions.

### 4. B2B Receivable

```text
Overdue Invoice → Revenue at Risk → Eligibility → Risk Assessment → LLM Diagnosis
→ Reminder / Escalation → Policy Authorization → Communication → Promise / Outcome → Audit
```

B2B recovery supports payment reminders, follow-ups, escalation, and promise-to-pay workflows.

### 5. Mandate Failure

```text
Mandate Failure → Revenue at Risk → Eligibility → Risk Prediction → LLM Recommendation
→ Policy Authorization → NACH Re-Presentation → Communication → Outcome → Audit
```

The mandate workflow supports bounded NACH re-presentment through the payment recovery layer.

### 6. Promise to Pay

```text
Promise to Pay → Payment Commitment → Monitor Outcome → Promise Fulfilled?
   ├── YES → Recovered
   └── NO  → Reminder → Escalation → Audit
```

The system can handle promise collection, payment reminders, escalation, and outcome tracking.

---

## 🤖 AI Decision Architecture

RecoverAI combines two intelligence layers.

### Advanced ML

The ML layer evaluates structured transaction features and produces:

- `recovery_probability`
- `risk_score`
- `risk_level`
- `expected_recovery_value`

Risk scores are represented on a `0–100` scale.

### Fine-Tuned LLM

RecoverAI uses a fine-tuned local language model for recovery reasoning.

| Component | Value |
|---|---|
| Base Model | `Qwen/Qwen2.5-0.5B-Instruct` |
| Fine-Tuning | LoRA |
| Adapter | `backend/llm/models/recoverai-lora` |

The LLM produces structured recovery intelligence such as agent diagnosis, recommended action, confidence, reason, and recovery strategy.

The LLM recommendation is **advisory** — it cannot bypass the Policy Governance layer.

---

## 🛡️ Policy Governance

Policy Governance is the final authorization layer before execution.

```text
AI Recommendation → Policy Evaluation
                        ├── BLOCK → Audit
                        └── ALLOW → Execute
```

Policy controls include:

- Recovery eligibility
- Retry limits
- Recovery amount limits
- Recovery time windows
- Payment status
- Risk thresholds
- Mandate status
- B2B overdue conditions
- Promise-to-pay conditions
- Case-specific action restrictions
- Escalation rules

**Example:**

```text
AI: "Retry payment"
        ↓
Policy checks:
  • Eligible?
  • Retry limit exceeded?
  • Payment already successful?
  • Risk acceptable?
  • Amount within configured limit?
  • Recovery window valid?
        ↓
ALLOW / BLOCK / ESCALATE
```

This creates a non-bypassable authorization boundary around AI-generated financial actions.

---

## 💳 Razorpay Integration

RecoverAI includes a dedicated payment adapter layer for Razorpay integration.

```text
RecoverAI → Payment Adapter
              ├── Simulation Mode
              └── Test Mode → Razorpay Adapter → Razorpay Test APIs
```

The payment layer supports:

- Order creation
- Payment retry workflows
- Idempotency
- Payment status handling
- Webhook verification
- HMAC-SHA256 signature verification
- Adapter-based gateway abstraction

Configuration is loaded from environment variables rather than hard-coded credentials.

> Razorpay integration is implemented through an adapter architecture so the recovery engine is not tightly coupled to a single payment provider.

---

## 📡 Payment Webhook Security

Webhook verification uses HMAC-SHA256.

```text
Razorpay Webhook → Receive Payload → Generate HMAC-SHA256 → Compare Signature
                                                                  ├── Valid → Process
                                                                  └── Invalid → Reject
```

This prevents unverified webhook events from being treated as trusted payment events.

---

## 📢 Multi-Channel Communication

RecoverAI supports a communication abstraction layer for:

- 📞 Voice
- 💬 WhatsApp
- 📧 Email
- 📱 SMS

```text
Recovery Decision → Communication Router → Voice / WhatsApp / Email / SMS
```

The communication architecture supports explicit provider states:

- `SIMULATED`
- `TEST_CONNECTED`
- `LIVE_CONNECTED`
- `NOT_CONFIGURED`

Simulated communication is clearly represented as simulated and is not presented as real customer delivery.

---

## 📊 Revenue Intelligence

RecoverAI converts recovery activity into measurable revenue intelligence.

**Key metrics:**

- Revenue at Risk
- Recovery Attempts
- Successful Recoveries
- Recovered Revenue
- Recovery Rate
- Blocked Actions
- Escalated Cases
- Recovery Probability
- Expected Recovery Value
- Risk Distribution

```text
Revenue at Risk → Recovery Opportunities → Eligible Cases → Recovery Attempts
→ Successful Recoveries → Recovered Revenue
```

---

## 📈 Batch Recovery Metrics

RecoverAI evaluates recovery performance across batches of cases.

```text
Batch
 ├── Payment Failures
 ├── Checkout Abandonments
 ├── Failed Subscriptions
 ├── B2B Receivables
 ├── Mandate Failures
 └── Promise to Pay
       ↓
  Recovery Engine → Batch Outcomes → Recovery Metrics
```

This enables comparison between total cases, eligible cases, recovery attempts, successful recoveries, failed recoveries, blocked actions, and recovered amount.

---

## 🧾 Audit Trail

Every recovery decision is designed to be traceable. The audit lifecycle captures:

| Field | Field | Field |
|---|---|---|
| Transaction | Customer | Case Type |
| Amount | Payment Status | Failure Reason |
| Risk Score | Risk Level | LLM Diagnosis |
| AI Action | AI Confidence | AI Reason |
| Policy Decision | Policy Reason | Execution Status |
| Recovery Status | Recovered Amount | Execution Message |
| Communication Attempts | Execution Timestamp | |

The audit trail allows the complete decision lifecycle to be reconstructed:

```text
What happened? → Why was it risky? → What did the AI recommend?
→ What did policy decide? → What was executed? → Was the customer contacted?
→ Was revenue recovered?
```

---

## 🖥️ RecoverAI Dashboard

The frontend provides a complete recovery intelligence dashboard with the following pages:

1. Overview
2. Transactions
3. AI Decisions
4. Risk Analysis
5. Pipeline Simulator
6. Recovery Opportunities
7. Policy Center
8. Execution
9. Audit Log

The dashboard provides visibility into the entire recovery lifecycle.

---

## 🔄 Decision Lifecycle

A single recovery case follows this lifecycle:

```text
Revenue Event
     ↓
Revenue at Risk
     ↓
Eligibility Check
     ↓
ML Risk Prediction
     ↓
Fine-Tuned LLM Diagnosis
     ↓
AI Recommendation
     ↓
Policy Governance
     ├── BLOCK
     └── ALLOW → Bounded Execution → Communication
     ↓
Outcome
     ↓
Audit Trail
     ↓
Recovery Metrics
```

---

## 🧩 Technology Stack

**Frontend**
- React
- Vite
- JavaScript
- Responsive Dashboard UI
- REST API integration

**Backend**
- Python
- FastAPI
- Pydantic
- SQLAlchemy layer
- CSV / JSON persistence

**AI / ML**
- Python
- Scikit-learn / ML pipeline
- Qwen/Qwen2.5-0.5B-Instruct
- LoRA fine-tuning
- Hugging Face Transformers
- PEFT

**Payments**
- Razorpay
- Razorpay Python SDK
- Payment adapter abstraction
- Webhook verification
- Sandbox/simulation recovery workflows

**Communication**
- Email (SMTP provider)
- SMS abstraction
- WhatsApp abstraction
- Voice abstraction

---

## 📁 Project Structure

```text
Razorpay/
│
├── backend/
│   ├── main.py
│   │
│   ├── schemas/
│   │   └── ...
│   │
│   ├── services/
│   │   ├── preprocessing.py
│   │   ├── eligibility_engine.py
│   │   ├── policy_engine.py
│   │   ├── recovery_orchestrator.py
│   │   ├── domain_executor.py
│   │   └── ...
│   │
│   ├── ml/
│   │   ├── features.py
│   │   ├── model.py
│   │   └── ...
│   │
│   ├── llm/
│   │   ├── model_adapter.py
│   │   ├── models/
│   │   │   └── recoverai-lora/
│   │   └── ...
│   │
│   ├── payment/
│   │   ├── razorpay_adapter.py
│   │   └── ...
│   │
│   ├── communications/
│   │   └── ...
│   │
│   ├── database/
│   │   └── ...
│   │
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── api.js
│   │   └── ...
│   │
│   ├── package.json
│   └── vite.config.js
│
├── tests/
│   └── ...
│
├── .env
├── .gitignore
└── README.md
```

---

## ⚙️ Environment Configuration

Create a `.env` file in the project root:

```ini
RECOVERY_MODE=simulation

LLM_PROVIDER=simulation
LLM_MODEL=recoverai-llm-v1
LLM_API_KEY=

RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
```

For local development, simulation mode can be used without external payment credentials.

> **Note:** Razorpay credentials should be stored only in `.env` and should never be committed to Git.

---

## 🚦 Running RecoverAI

### 1. Start the FastAPI Backend

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Backend available at: `http://127.0.0.1:8000`

### 2. Start the React Frontend

```bash
cd frontend
npm run dev
```

### 3. Build the Frontend

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

The test suite covers:

- Recovery flows
- Policy decisions
- ML pipeline
- LLM integration
- Payment adapters
- Razorpay webhook verification
- Communication providers
- Execution
- Audit logging
- API endpoints
- Schemas
- Batch recovery
- Orchestration

---

## 🔌 API Endpoints

**System**
```text
GET /health
GET /api/model-info
```

**Dashboard & Analytics**
```text
GET /api/dashboard
GET /api/metrics
GET /api/transactions
GET /api/decisions
GET /api/execution
GET /api/audit
GET /api/risk
```

**Recovery**
```text
POST /api/recovery/predict
POST /api/recovery/evaluate
POST /api/recovery/execute
```

**Machine Learning**
```text
POST /api/ml/predict
```

**LLM**
```text
POST /api/llm/decision
```

**Payment**
```text
POST /api/payment/create
POST /api/payment/retry
```

**Communication**
```text
POST /api/communication/send
```

---

## 🔐 Security & Governance Principles

RecoverAI follows several important principles for AI-driven financial workflows.

1. **AI Does Not Directly Execute** — The LLM generates recommendations; the Policy Engine determines whether those recommendations are permitted.
2. **Bounded Execution** — Execution is limited to supported recovery actions.
3. **Stopping Rules** — Recovery attempts stop when configured limits or disqualifying conditions are reached.
4. **Risk-Based Escalation** — High-risk cases can be blocked or escalated instead of being automatically executed.
5. **Payment Verification** — Payment webhook signatures are verified before processing trusted payment events.
6. **Secret Management** — Credentials are loaded through environment variables and should not be committed to source control.
7. **Communication Transparency** — Simulated communication is explicitly represented as simulated.

---

## 🧪 Example Recovery Case

**Example input:**

```json
{
  "transaction_id": "txn_1001",
  "customer_id": "cust_501",
  "amount": 4999,
  "case_type": "PAYMENT_FAILURE",
  "payment_status": "failed",
  "failure_reason": "insufficient_funds"
}
```

**Processing lifecycle:**

```text
Transaction → Preprocessing → Eligibility → ML Prediction → Risk Score
→ LLM Diagnosis → Recommendation → Policy Check → Payment Retry
→ Communication → Recovery Outcome → Audit
```

**Possible outcome:**

```text
Recovery Status: RECOVERED
Recovered Amount: ₹4,999
```

---

## 💡 Why RecoverAI?

Traditional payment systems generally focus on a single step:

```text
Payment Failed → Retry
```

RecoverAI introduces an intelligent recovery lifecycle instead:

```text
Payment Failed
      ↓
Why did it fail?
      ↓
Is recovery appropriate?
      ↓
How likely is recovery?
      ↓
What intervention should be used?
      ↓
Is the intervention allowed?
      ↓
Execute bounded action
      ↓
Communicate with customer
      ↓
Measure recovered revenue
      ↓
Audit the entire decision
```

This transforms recovery from a simple retry mechanism into a **policy-governed AI revenue recovery system**.

---

## 📊 Unified Recovery Engine

All six case types use the same high-level engine:

```text
Recovery Event → Detection → Revenue at Risk → Eligibility → ML Prediction
→ LLM Diagnosis → Recommendation → Policy Governance
                                       ├── BLOCK
                                       └── ALLOW → Execution → Communication
                                       ↓
                                    Outcome → Audit → Metrics
```

The same architecture can handle different revenue-loss events while using domain-specific execution rules.

---

## 🎬 Demo Flow

A recommended RecoverAI demonstration follows this sequence:

1. Overview Dashboard
2. Revenue at Risk
3. Select Recovery Opportunity
4. Show ML Risk
5. Show LLM Recommendation
6. Show Policy Decision
7. Execute Recovery
8. Show Communication
9. Show Recovery Outcome
10. Show Audit Log
11. Show Recovered Revenue

This demonstrates that RecoverAI does not simply predict a problem — it takes the recovery decision through the complete controlled lifecycle.

---

## 🏆 Hackathon Value Proposition

RecoverAI combines **AI, Machine Learning, a Fine-Tuned LLM, Policy Governance, Razorpay Payment Infrastructure, Automated Recovery, Customer Communication, Auditability, and Revenue Intelligence** into one platform.

The result is a recovery engine that answers four critical questions:

```text
What revenue is at risk?
        ↓
Why is it at risk?
        ↓
What should we do?
        ↓
Did we actually recover the money?
```

---

## 🔮 Future Enhancements

- Production Razorpay integration
- Real-time payment event ingestion
- More advanced recovery models
- Reinforcement learning for intervention selection
- Adaptive communication strategies
- Real WhatsApp integration
- Real SMS provider integration
- Real voice recovery
- Human-in-the-loop approval workflows
- Advanced revenue forecasting
- Unified production database
- Real-time analytics
- Multi-currency recovery
- Customer-level recovery intelligence
- Automated recovery strategy optimization

---

## ⚠️ Implementation Disclosure

RecoverAI is designed as a hackathon-ready AI revenue recovery platform. Depending on the configured environment:

- Payment workflows may run in simulation/test mode.
- Communication channels may operate in simulated mode.
- External provider credentials may not be configured.
- Production payment and communication integrations require appropriate provider credentials and deployment configuration.

The architecture is designed so simulated components can be replaced with connected providers without changing the core recovery orchestration model.

---

## 📌 Core Principle

> **RecoverAI doesn't just identify lost revenue.**
>
> It determines what can be recovered, decides how to recover it, ensures the action is policy-authorized, executes the bounded recovery workflow, measures the result, and records the complete decision trail.

---

## 🚀 RecoverAI

### Turning Revenue at Risk into Revenue Recovered.

**AI recommends. Policy authorizes. Executor executes. Revenue gets recovered.**
