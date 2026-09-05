import { useEffect, useState } from "react"
import {
    getDashboard,
    getMetrics,
    getTransactions,
    getDecisions,
    getExecution,
    getAudit,
    getRisk,
    predictRecovery,
    evaluateRecovery
} from "./api"
import "./App.css"

function fmt(value) { return Number(value || 0).toLocaleString("en-IN") }
function formatRupees(value) { return "\u20B9" + fmt(value) }
function safeStr(v) { if (v === null || v === undefined || v === "") return "-"; return String(v) }
function safeNum(v) { const n = Number(v); return isNaN(n) ? 0 : n }

function StatusBadge({ value }) {
    const v = safeStr(value).toLowerCase()
    let cls = "status-badge"
    if (v === "success" || v === "recovered" || v === "simulated_delivered" || v === "simulated_sent") cls += " success"
    else if (v === "failed" || v === "failure") cls += " failed"
    else if (v === "abandoned" || v === "follow_up") cls += " abandoned"
    else if (v === "executed" || v === "simulated") cls += " executed"
    else if (v === "blocked") cls += " blocked"
    return <span className={cls}>{safeStr(value)}</span>
}

function RiskBadge({ value }) {
    const v = safeStr(value).toLowerCase()
    return <span className={"risk-badge " + v}>{safeStr(value) || "low"}</span>
}

function ActionBadge({ value }) {
    return <span className="action-badge">{safeStr(value)}</span>
}

function StatCard({ icon, title, value, sub, accent }) {
    return (
        <div className="card">
            <div className={"card-icon" + (accent ? " " + accent : "")}>{icon}</div>
            <div className="card-title">{title}</div>
            <div className="card-value">{value}</div>
            {sub && <div className="card-sub">{sub}</div>}
        </div>
    )
}

function SummaryBar({ items }) {
    return (
        <div className="summary">
            {items.map((item, i) => (
                <div key={i}>
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                </div>
            ))}
        </div>
    )
}

function Section({ title, sub, badge, children }) {
    return (
        <div className="section">
            <div className="section-header">
                <div>
                    <h2>{title}</h2>
                    {sub && <p>{sub}</p>}
                </div>
                {badge && <span className="evaluation">{badge}</span>}
            </div>
            {children}
        </div>
    )
}

function isEligible(v) { return v === true || safeStr(v).toLowerCase() === "true" }

function EligibleBadge({ value }) {
    return <span className={isEligible(value) ? "eligible-yes" : "eligible-no"}>{isEligible(value) ? "Yes" : "No"}</span>
}

function DataTable({ data }) {
    if (!data || !data.items || data.items.length === 0) return <div className="empty">No records available.</div>
    const items = data.items
    return (
        <div className="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>TRANSACTION</th><th>CUSTOMER</th><th>AMOUNT</th><th>STATUS</th>
                        <th>RISK</th><th>AI DIAGNOSIS</th><th>ACTION</th><th>CONFIDENCE</th>
                    </tr>
                </thead>
                <tbody>
                    {items.slice(0, 50).map((item, i) => (
                        <tr key={item.transaction_id || i}>
                            <td><strong>{safeStr(item.transaction_id)}</strong></td>
                            <td>{safeStr(item.customer_id)}</td>
                            <td>{formatRupees(item.amount)}</td>
                            <td><StatusBadge value={item.payment_status} /></td>
                            <td><RiskBadge value={item.risk_level} /></td>
                            <td className="diagnosis">{safeStr(item.agent_diagnosis)}</td>
                            <td><ActionBadge value={item.agent_action || item.recommended_action} /></td>
                            <td>{item.agent_confidence != null ? (safeNum(item.agent_confidence) * 100).toFixed(0) + "%" : "-"}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

function TransactionsTable({ data }) {
    const [search, setSearch] = useState("")
    const [statusFilter, setStatusFilter] = useState("all")
    const [riskFilter, setRiskFilter] = useState("all")
    const [eligibleFilter, setEligibleFilter] = useState("all")

    if (!data || !data.items || data.items.length === 0) return <div className="empty">No records available.</div>

    const statuses = ["all", ...new Set(data.items.map(i => i.payment_status).filter(Boolean))]
    const risks = ["all", "low", "medium", "high"]

    let items = data.items
    if (search) {
        const q = search.toLowerCase()
        items = items.filter(i =>
            safeStr(i.transaction_id).toLowerCase().includes(q) ||
            safeStr(i.customer_id).toLowerCase().includes(q) ||
            safeStr(i.failure_reason).toLowerCase().includes(q)
        )
    }
    if (statusFilter !== "all") items = items.filter(i => safeStr(i.payment_status).toLowerCase() === statusFilter)
    if (riskFilter !== "all") items = items.filter(i => safeStr(i.risk_level).toLowerCase() === riskFilter)
    if (eligibleFilter !== "all") items = items.filter(i => eligibleFilter === "yes" ? isEligible(i.recovery_eligible) : !isEligible(i.recovery_eligible))

    return (
        <div>
            <div className="filters">
                <input className="filter-input" type="text" placeholder="Search transaction, customer, reason..." value={search} onChange={e => setSearch(e.target.value)} />
                <select className="filter-select" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
                    {statuses.map(s => <option key={s} value={s}>{s === "all" ? "All Status" : s}</option>)}
                </select>
                <select className="filter-select" value={riskFilter} onChange={e => setRiskFilter(e.target.value)}>
                    {risks.map(r => <option key={r} value={r}>{r === "all" ? "All Risk" : r}</option>)}
                </select>
                <select className="filter-select" value={eligibleFilter} onChange={e => setEligibleFilter(e.target.value)}>
                    <option value="all">All Recovery</option>
                    <option value="yes">Eligible</option>
                    <option value="no">Not Eligible</option>
                </select>
                <span className="filter-count">{items.length} records</span>
            </div>
            <div className="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>TRANSACTION</th><th>CUSTOMER</th><th>AMOUNT</th><th>STATUS</th>
                            <th>FAILURE REASON</th><th>ATTEMPTS</th><th>ELIGIBLE</th><th>RISK</th><th>RECOMMENDED ACTION</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.slice(0, 100).map((item, i) => (
                            <tr key={item.transaction_id || i}>
                                <td><strong>{safeStr(item.transaction_id)}</strong></td>
                                <td>{safeStr(item.customer_id)}</td>
                                <td>{formatRupees(item.amount)}</td>
                                <td><StatusBadge value={item.payment_status} /></td>
                                <td>{safeStr(item.failure_reason)}</td>
                                <td>{safeStr(item.attempt_count)}</td>
                                <td><EligibleBadge value={item.recovery_eligible} /></td>
                                <td><RiskBadge value={item.risk_level} /></td>
                                <td><ActionBadge value={item.recommended_action || item.agent_action} /></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

function DecisionsTable({ items }) {
    if (!items || items.length === 0) return <div className="empty">No records available.</div>
    return (
        <div className="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>TRANSACTION</th><th>CUSTOMER</th><th>AMOUNT</th><th>STATUS</th>
                        <th>RISK</th><th>AI DIAGNOSIS</th><th>ACTION</th><th>CONFIDENCE</th>
                    </tr>
                </thead>
                <tbody>
                    {items.slice(0, 100).map((item, i) => (
                        <tr key={item.transaction_id || i}>
                            <td><strong>{safeStr(item.transaction_id)}</strong></td>
                            <td>{safeStr(item.customer_id)}</td>
                            <td>{formatRupees(item.amount)}</td>
                            <td><StatusBadge value={item.payment_status} /></td>
                            <td><RiskBadge value={item.risk_level} /></td>
                            <td className="diagnosis">{safeStr(item.agent_diagnosis)}</td>
                            <td><ActionBadge value={item.agent_action || item.recommended_action} /></td>
                            <td>{item.agent_confidence != null ? (safeNum(item.agent_confidence) * 100).toFixed(0) + "%" : "-"}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

function ExecutionTable({ items }) {
    if (!items || items.length === 0) return <div className="empty">No records available.</div>
    return (
        <div className="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>TRANSACTION</th><th>ACTION</th><th>EXECUTION STATUS</th>
                        <th>RECOVERY STATUS</th><th>AMOUNT</th><th>POLICY RESULT</th><th>TIMESTAMP</th>
                    </tr>
                </thead>
                <tbody>
                    {items.slice(0, 100).map((item, i) => (
                        <tr key={item.transaction_id || i}>
                            <td><strong>{safeStr(item.transaction_id)}</strong></td>
                            <td><ActionBadge value={item.agent_action} /></td>
                            <td><StatusBadge value={item.execution_status} /></td>
                            <td><StatusBadge value={item.recovery_status} /></td>
                            <td>{formatRupees(item.amount)}</td>
                            <td className="diagnosis">{safeStr(item.policy_reason || item.execution_message)}</td>
                            <td className="timestamp">{safeStr(item.executed_at)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

function AuditTable({ items }) {
    if (!items || items.length === 0) return <div className="empty">No records available.</div>
    return (
        <div className="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>TRANSACTION</th><th>CUSTOMER</th><th>AGENT ACTION</th>
                        <th>POLICY</th><th>EXECUTION</th><th>RECOVERY</th><th>MESSAGE</th><th>TIMESTAMP</th>
                    </tr>
                </thead>
                <tbody>
                    {items.slice(0, 100).map((item, i) => (
                        <tr key={item.transaction_id || i}>
                            <td><strong>{safeStr(item.transaction_id)}</strong></td>
                            <td>{safeStr(item.customer_id)}</td>
                            <td><ActionBadge value={item.agent_action} /></td>
                            <td><span className={safeStr(item.policy_decision) === "ALLOW" ? "eligible-yes" : "eligible-no"}>{safeStr(item.policy_decision)}</span></td>
                            <td><StatusBadge value={item.execution_status} /></td>
                            <td><StatusBadge value={item.recovery_status} /></td>
                            <td className="diagnosis">{safeStr(item.execution_message || item.policy_reason)}</td>
                            <td className="timestamp">{safeStr(item.executed_at)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

function RiskTable({ items }) {
    if (!items || items.length === 0) return <div className="empty">No records available.</div>
    return (
        <div className="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>TRANSACTION</th><th>CUSTOMER</th><th>AMOUNT</th><th>RISK SCORE</th>
                        <th>RISK LEVEL</th><th>FAILURE REASON</th><th>ELIGIBLE</th><th>RECOMMENDED ACTION</th>
                    </tr>
                </thead>
                <tbody>
                    {items.slice(0, 100).map((item, i) => (
                        <tr key={item.transaction_id || i}>
                            <td><strong>{safeStr(item.transaction_id)}</strong></td>
                            <td>{safeStr(item.customer_id)}</td>
                            <td>{formatRupees(item.amount)}</td>
                            <td><strong>{safeStr(item.risk_score)}</strong></td>
                            <td><RiskBadge value={item.risk_level} /></td>
                            <td>{safeStr(item.failure_reason)}</td>
                            <td><EligibleBadge value={item.recovery_eligible} /></td>
                            <td><ActionBadge value={item.recommended_action || item.agent_action} /></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

function SimulatorView({ onSimulate }) {
    const [txId, setTxId] = useState("TX_ORCH_99")
    const [custId, setCustId] = useState("CUST1099")
    const [amount, setAmount] = useState(1999)
    const [status, setStatus] = useState("failed")
    const [reason, setReason] = useState("timeout")
    const [attempts, setAttempts] = useState(1)
    const [prevPayments, setPrevPayments] = useState(4)
    const [prevFailures, setPrevFailures] = useState(1)
    const [days, setDays] = useState(2)
    const [subStatus, setSubStatus] = useState("active")

    const [loading, setLoading] = useState(false)
    const [orchestration, setOrchestration] = useState(null)
    const [error, setError] = useState("")

    async function handleSubmit(e) {
        e.preventDefault()
        setLoading(true)
        setError("")
        setOrchestration(null)

        const payload = {
            transaction_id: txId,
            customer_id: custId,
            amount: Number(amount),
            payment_status: status,
            failure_reason: reason,
            attempt_count: Number(attempts),
            customer_previous_payments: Number(prevPayments),
            customer_previous_failures: Number(prevFailures),
            days_since_event: Number(days),
            subscription_status: subStatus
        }

        try {
            const res = await fetch("http://127.0.0.1:8000/api/recovery/execute", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })
            if (!res.ok) throw new Error("Orchestration API failed")
            const data = await res.json()
            setOrchestration(data)
            if (onSimulate) onSimulate()
        } catch (err) {
            setError(err.message || "Failed to run recovery simulation.")
        } finally {
            setLoading(false)
        }
    }

    const pRes = orchestration?.pipeline_result

    return (
        <div className="section">
            <div className="section-header">
                <div>
                    <h2>Unified Multi-Channel Recovery Pipeline Simulator</h2>
                    <p>Execute real-time ML inference, LLM decisions, policy governance, payment sandbox & multi-channel recovery.</p>
                </div>
                <span className="evaluation">SIMULATION MODE</span>
            </div>

            <form onSubmit={handleSubmit} className="filters" style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px" }}>
                <div>
                    <label style={{ fontSize: "12px", fontWeight: "600", color: "#64748b" }}>Transaction ID</label>
                    <input className="filter-input" style={{ width: "100%" }} type="text" value={txId} onChange={e => setTxId(e.target.value)} required />
                </div>
                <div>
                    <label style={{ fontSize: "12px", fontWeight: "600", color: "#64748b" }}>Customer ID</label>
                    <input className="filter-input" style={{ width: "100%" }} type="text" value={custId} onChange={e => setCustId(e.target.value)} required />
                </div>
                <div>
                    <label style={{ fontSize: "12px", fontWeight: "600", color: "#64748b" }}>Amount (₹)</label>
                    <input className="filter-input" style={{ width: "100%" }} type="number" value={amount} onChange={e => setAmount(e.target.value)} required />
                </div>
                <div>
                    <label style={{ fontSize: "12px", fontWeight: "600", color: "#64748b" }}>Payment Status</label>
                    <select className="filter-select" style={{ width: "100%" }} value={status} onChange={e => setStatus(e.target.value)}>
                        <option value="failed">failed</option>
                        <option value="abandoned">abandoned</option>
                        <option value="success">success</option>
                    </select>
                </div>
                <div>
                    <label style={{ fontSize: "12px", fontWeight: "600", color: "#64748b" }}>Failure Reason</label>
                    <select className="filter-select" style={{ width: "100%" }} value={reason} onChange={e => setReason(e.target.value)}>
                        <option value="timeout">timeout</option>
                        <option value="network_error">network_error</option>
                        <option value="upi_failure">upi_failure</option>
                        <option value="bank_declined">bank_declined</option>
                        <option value="insufficient_funds">insufficient_funds</option>
                        <option value="authentication_failed">authentication_failed</option>
                    </select>
                </div>
                <div>
                    <label style={{ fontSize: "12px", fontWeight: "600", color: "#64748b" }}>Attempt Count</label>
                    <input className="filter-input" style={{ width: "100%" }} type="number" value={attempts} onChange={e => setAttempts(e.target.value)} required />
                </div>
                <div>
                    <label style={{ fontSize: "12px", fontWeight: "600", color: "#64748b" }}>Previous Successes</label>
                    <input className="filter-input" style={{ width: "100%" }} type="number" value={prevPayments} onChange={e => setPrevPayments(e.target.value)} required />
                </div>
                <div>
                    <label style={{ fontSize: "12px", fontWeight: "600", color: "#64748b" }}>Previous Failures</label>
                    <input className="filter-input" style={{ width: "100%" }} type="number" value={prevFailures} onChange={e => setPrevFailures(e.target.value)} required />
                </div>
                <div>
                    <label style={{ fontSize: "12px", fontWeight: "600", color: "#64748b" }}>Days Since Event</label>
                    <input className="filter-input" style={{ width: "100%" }} type="number" value={days} onChange={e => setDays(e.target.value)} required />
                </div>
                <div style={{ gridColumn: "span 3" }}>
                    <button className="retry" type="submit" disabled={loading} style={{ width: "100%", padding: "14px", fontSize: "15px" }}>
                        {loading ? "Running Complete Recovery Orchestrator..." : "⚡ Run Unified Pipeline Execution"}
                    </button>
                </div>
            </form>

            {error && <div className="error-box" style={{ marginTop: "20px" }}><p>{error}</p></div>}

            {orchestration && (
                <div style={{ marginTop: "28px" }}>
                    <h3 style={{ margin: "0 0 16px", color: "#1e293b" }}>Pipeline Visualization & Multi-Channel Recovery Summary</h3>

                    {/* Stage by Stage Flow Visualization */}
                    <div className="summary" style={{ gridTemplateColumns: "repeat(5, 1fr)", marginBottom: "20px" }}>
                        <div><span>1. Eligibility</span><strong><EligibleBadge value={pRes.eligibility.eligible} /></strong></div>
                        <div><span>2. ML Risk</span><strong>{pRes.risk.risk_score} (<RiskBadge value={pRes.risk.risk_level} />)</strong></div>
                        <div><span>3. LLM Action</span><strong><ActionBadge value={pRes.decision.action} /></strong></div>
                        <div><span>4. Policy Governance</span><strong><span className={pRes.policy.allowed ? "eligible-yes" : "eligible-no"}>{pRes.policy.policy_status}</span></strong></div>
                        <div><span>5. Recovery Status</span><strong><StatusBadge value={pRes.execution.recovery_status} /></strong></div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "20px" }}>
                        {/* AI Intelligence & Policy */}
                        <div style={{ background: "white", padding: "20px", borderRadius: "16px", border: "1px solid #e2e8f0" }}>
                            <h4 style={{ margin: "0 0 12px", color: "#1e293b" }}>🤖 AI & Governance Intelligence</h4>
                            <p style={{ fontSize: "14px", margin: "4px 0" }}><strong>ML Prob:</strong> {(safeNum(orchestration.ml_insights?.recovery_probability) * 100).toFixed(1)}% | <strong>Expected Value:</strong> {formatRupees(orchestration.ml_insights?.expected_recovery_value)}</p>
                            <p style={{ fontSize: "14px", margin: "4px 0" }}><strong>Diagnosis:</strong> {pRes.decision.diagnosis}</p>
                            <p style={{ fontSize: "14px", margin: "4px 0" }}><strong>Reason:</strong> {pRes.decision.reason}</p>
                            <p style={{ fontSize: "14px", margin: "4px 0", color: pRes.policy.allowed ? "#166534" : "#991b1b" }}><strong>Policy:</strong> {pRes.policy.reason}</p>
                        </div>

                        {/* Multi-Channel Recovery Status */}
                        <div style={{ background: "white", padding: "20px", borderRadius: "16px", border: "1px solid #e2e8f0" }}>
                            <h4 style={{ margin: "0 0 12px", color: "#1e293b" }}>📡 Multi-Channel Communications</h4>
                            {orchestration.communications && orchestration.communications.length > 0 ? (
                                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                                    {orchestration.communications.map((c, idx) => (
                                        <div key={idx} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#f8fafc", padding: "10px 14px", borderRadius: "10px" }}>
                                            <div>
                                                <strong style={{ textTransform: "uppercase", fontSize: "12px", color: "#475569" }}>{c.channel}</strong>
                                                <p style={{ margin: "2px 0 0", fontSize: "13px", color: "#334155" }}>{c.delivery_message}</p>
                                            </div>
                                            <StatusBadge value={c.status} />
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p style={{ color: "#94a3b8", fontSize: "14px" }}>No communication channels dispatched (Policy Blocked or Ineligible).</p>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

function App() {
    const [page, setPage] = useState("overview")
    const [dashboard, setDashboard] = useState(null)
    const [metrics, setMetrics] = useState(null)
    const [transactions, setTransactions] = useState(null)
    const [decisions, setDecisions] = useState(null)
    const [execution, setExecution] = useState(null)
    const [audit, setAudit] = useState(null)
    const [risk, setRisk] = useState(null)
    const [loading, setLoading] = useState(true)
    const [evaluating, setEvaluating] = useState(false)
    const [coreError, setCoreError] = useState("")

    async function loadData() {
        try {
            setLoading(true)
            setCoreError("")
            const [dashboardData, metricsData, transactionsData] = await Promise.all([
                getDashboard(), getMetrics(), getTransactions()
            ])
            setDashboard(dashboardData)
            setMetrics(metricsData)
            setTransactions(transactionsData)
            await Promise.allSettled([
                getDecisions().then(setDecisions).catch(() => {}),
                getExecution().then(setExecution).catch(() => {}),
                getAudit().then(setAudit).catch(() => {}),
                getRisk().then(setRisk).catch(() => {}),
            ])
        } catch (err) {
            console.error(err)
            setCoreError("Could not connect to RecoverAI backend.")
        } finally {
            setLoading(false)
        }
    }

    async function handleRunEvaluation() {
        try {
            setEvaluating(true)
            await evaluateRecovery()
            await loadData()
        } catch (err) {
            alert("Evaluation failed: " + err.message)
        } finally {
            setEvaluating(false)
        }
    }

    useEffect(() => { loadData() }, [])

    function renderOverview() {
        if (!dashboard || !metrics) return <div className="loading">Loading dashboard...</div>
        return (
            <>
                <div className="page-header">
                    <div>
                        <div className="breadcrumb">Control Center / Overview</div>
                        <h1>AI Revenue Recovery</h1>
                        <p>Monitor failed payments, ML risk signals, LLM recovery decisions and multi-channel actions.</p>
                    </div>
                    <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                        <button className="retry" onClick={handleRunEvaluation} disabled={evaluating} style={{ padding: "8px 16px", fontSize: "13px" }}>
                            {evaluating ? "Evaluating..." : "↻ Run Batch Evaluation"}
                        </button>
                        <div className="live">{"● LIVE"}</div>
                    </div>
                </div>
                <div className="environment">Evaluation Environment (Simulation & Sandbox Mode)</div>
                <div className="cards">
                    <StatCard icon={"\u20B9"} title="Revenue at Risk" value={formatRupees(dashboard.revenue_at_risk)} sub={<><>At risk <strong>{dashboard.recovery_eligible}</strong> eligible</></>} />
                    <StatCard icon={"✓"} accent="success" title="Recovered Revenue" value={formatRupees(dashboard.recovered_amount)} sub={<><>Recovered <strong>{metrics.successful_recoveries || 0}</strong> transactions</></>} />
                    <StatCard icon={"↗"} title="Recovery Attempts" value={dashboard.recovery_attempts} sub={metrics.attempt_success_rate + "% success AI initiated"} />
                    <StatCard icon={"⊘"} title="Policy Blocked" value={dashboard.blocked_actions} sub="Protected · Policy enforcement" />
                </div>
                <Section title="Recovery Performance" sub="AI recovery evaluation metrics" badge="HELD-OUT EVALUATION">
                    <div className="metrics">
                        <div className="metric"><span>Recovery Rate</span><strong>{metrics.recovery_rate}%</strong><small>Successful recoveries / eligible transactions</small></div>
                        <div className="metric"><span>Attempt Success</span><strong>{metrics.attempt_success_rate}%</strong><small>Successful recoveries / recovery attempts</small></div>
                        <div className="metric"><span>Revenue Recovery</span><strong>{metrics.revenue_recovery_rate}%</strong><small>Recovered revenue / revenue at risk</small></div>
                    </div>
                </Section>
                <Section title="System Summary" sub="Current evaluation state">
                    <SummaryBar items={[
                        { label: "Total Transactions", value: dashboard.total_transactions },
                        { label: "Failed / Abandoned", value: dashboard.failed_transactions },
                        { label: "Recovery Eligible", value: dashboard.recovery_eligible },
                        { label: "Revenue at Risk", value: formatRupees(dashboard.revenue_at_risk) },
                    ]} />
                </Section>
                {transactions && (
                    <Section title="Recent Transactions" sub="Latest payment activity" badge={transactions.count + " RECORDS"}>
                        <DataTable data={transactions} />
                    </Section>
                )}
            </>
        )
    }

    function renderPage() {
        switch (page) {
            case "overview":     return renderOverview()
            case "transactions": return <Section title="Transactions" sub="Payment activity"><TransactionsTable data={transactions} /></Section>
            case "decisions":    return <Section title="Decision Engine" sub="AI recovery recommendations"><DecisionsTable items={decisions?.items} /></Section>
            case "execution":    return <Section title="Execution Control Center" sub="Agent-executed actions"><ExecutionTable items={execution?.items} /></Section>
            case "audit":        return <Section title="Audit Log" sub="Complete activity trail"><AuditTable items={audit?.items} /></Section>
            case "risk":         return <Section title="Risk Analysis" sub="Transaction-level risk"><RiskTable items={risk?.items} /></Section>
            case "simulator":    return <SimulatorView onSimulate={loadData} />
            default:               return renderOverview()
        }
    }

    if (loading) {
        return (
            <div className="loading-screen">
                <div className="loading-card">
                    <div className="loading-logo">R</div>
                    <h2>RecoverAI</h2>
                    <p>Loading Revenue Intelligence...</p>
                </div>
            </div>
        )
    }

    if (coreError) {
        return (
            <div className="error-page">
                <div className="error-box">
                    <h2>RecoverAI</h2>
                    <p>{coreError}</p>
                    <button className="retry" onClick={loadData}>Retry Connection</button>
                </div>
            </div>
        )
    }

    return (
        <div className="app">
            <aside className="sidebar">
                <div className="brand">
                    <div className="brand-logo">R</div>
                    <div>
                        <div className="brand-name">RecoverAI</div>
                        <div className="brand-subtitle">Revenue Intelligence</div>
                    </div>
                </div>
                <div className="nav-section">
                    <h3 className="nav-heading">CONTROL CENTER</h3>
                    <button className={"nav-button" + (page === "overview" ? " active" : "")} onClick={() => setPage("overview")}> <span className="nav-icon">{"▦"}</span> Overview</button>
                    <button className={"nav-button" + (page === "simulator" ? " active" : "")} onClick={() => setPage("simulator")}> <span className="nav-icon">{"⚡"}</span> Simulator & Comms</button>
                    <button className={"nav-button" + (page === "transactions" ? " active" : "")} onClick={() => setPage("transactions")}> <span className="nav-icon">{"↗"}</span> Transactions</button>
                    <button className={"nav-button" + (page === "decisions" ? " active" : "")} onClick={() => setPage("decisions")}> <span className="nav-icon">{"✦"}</span> AI Decisions</button>
                    <button className={"nav-button" + (page === "execution" ? " active" : "")} onClick={() => setPage("execution")}> <span className="nav-icon">{"⚡"}</span> Execution</button>
                </div>
                <div className="nav-section">
                    <h3 className="nav-heading">GOVERNANCE</h3>
                    <button className={"nav-button" + (page === "audit" ? " active" : "")} onClick={() => setPage("audit")}> <span className="nav-icon">{"◉"}</span> Audit Log</button>
                    <button className={"nav-button" + (page === "risk" ? " active" : "")} onClick={() => setPage("risk")}> <span className="nav-icon">{"△"}</span> Risk Analysis</button>
                </div>
                <div className="sidebar-bottom">
                    <div className="system-status">
                        <div className="status-dot">{"●"}</div>
                        <div>
                            <strong>System Online</strong>
                            <span>All services operational</span>
                        </div>
                    </div>
                    <div className="version">RecoverAI v1.0.0</div>
                </div>
            </aside>
            <main className="main">
                {renderPage()}
            </main>
        </div>
    )
}

export default App
