// src/App.jsx
import { useEffect, useState } from "react";
import {
    getDashboard,
    getMetrics,
    getTransactions,
    getDecisions,
    getExecution,
    getAudit,
    getRisk,
    evaluateRecovery
} from "./api";
import "./index.css";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import OverviewPage from "./pages/OverviewPage";
import OpportunitiesPage from "./pages/OpportunitiesPage";
import PolicyPage from "./pages/PolicyPage";
import SimulatorView from "./components/SimulatorView";
import { ToastProvider, useToast } from "./components/ui/ToastProvider";
import {
  fmt,
  formatRupees,
  safeStr,
  safeNum,
  isEligible
} from "./utils";
import {
  StatusBadge,
  RiskBadge,
  ActionBadge,
  EligibleBadge
} from "./components/Badges";

function Section({ title, sub, badge, children }) {
  return (
    <div className="bg-white p-6 rounded-xl border border-[#DDE3DF] shadow-xs mb-6">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4 pb-3 border-b border-[#DDE3DF]">
        <div>
          <h2 className="text-xl font-bold text-[#173F35]">{title}</h2>
          {sub && <p className="text-xs text-[#68746F]">{sub}</p>}
        </div>
        {badge && (
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-[#E4F1EC] text-[#173F35]">
            {badge}
          </span>
        )}
      </div>
      {children}
    </div>
  );
}

function TransactionsTable({ data, onRowClick }) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [riskFilter, setRiskFilter] = useState("all");
  const [eligibleFilter, setEligibleFilter] = useState("all");

  if (!data || !data.items || data.items.length === 0) return <div className="p-8 text-center text-[#68746F]">No records available.</div>;

  const statuses = ["all", ...new Set(data.items.map(i => i.payment_status).filter(Boolean))];
  const risks = ["all", "low", "medium", "high"];

  let items = data.items;
  if (search) {
    const q = search.toLowerCase();
    items = items.filter(i =>
      safeStr(i.transaction_id).toLowerCase().includes(q) ||
      safeStr(i.customer_id).toLowerCase().includes(q) ||
      safeStr(i.failure_reason).toLowerCase().includes(q)
    );
  }
  if (statusFilter !== "all") items = items.filter(i => safeStr(i.payment_status).toLowerCase() === statusFilter);
  if (riskFilter !== "all") items = items.filter(i => safeStr(i.risk_level).toLowerCase() === riskFilter);
  if (eligibleFilter !== "all") items = items.filter(i => eligibleFilter === "yes" ? isEligible(i.recovery_eligible) : !isEligible(i.recovery_eligible));

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
        <span className="filter-count text-xs font-semibold text-[#68746F]">{items.length} records</span>
      </div>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>TRANSACTION</th><th>CUSTOMER</th><th>AMOUNT</th><th>STATUS</th>
              <th>FAILURE REASON</th><th>ATTEMPTS</th><th>ELIGIBLE</th><th>RISK</th><th>AI RECOMMENDS</th>
            </tr>
          </thead>
          <tbody>
            {items.slice(0, 100).map((item, i) => (
              <tr
                key={item.transaction_id || i}
                tabIndex={0}
                className="hover:bg-[#F7F5F0] cursor-pointer"
                onClick={() => onRowClick && onRowClick(item)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onRowClick && onRowClick(item);
                  }
                }}
              >
                <td><strong>{safeStr(item.transaction_id)}</strong></td>
                <td>{safeStr(item.customer_id)}</td>
                <td className="font-semibold text-[#173F35]">{formatRupees(item.amount)}</td>
                <td><StatusBadge value={item.payment_status} /></td>
                <td>{safeStr(item.failure_reason)}</td>
                <td>{safeStr(item.attempt_count)}</td>
                <td><EligibleBadge value={item.recovery_eligible} /></td>
                <td><RiskBadge value={item.risk_level} /></td>
                <td>
                  <div className="flex items-center gap-1">
                    <span className="text-[10px] text-[#68746F] uppercase font-bold">AI recommends:</span>
                    <ActionBadge value={item.recommended_action || item.agent_action} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DecisionsTable({ items, onRowClick }) {
  if (!items || items.length === 0) return <div className="p-8 text-center text-[#68746F]">No records available.</div>;
  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>TRANSACTION</th><th>CUSTOMER</th><th>AMOUNT</th><th>STATUS</th>
            <th>RISK</th><th>AI DIAGNOSIS</th><th>AI RECOMMENDS</th><th>CONFIDENCE</th>
          </tr>
        </thead>
        <tbody>
          {items.slice(0, 100).map((item, i) => (
            <tr
              key={item.transaction_id || i}
              tabIndex={0}
              className="hover:bg-[#F7F5F0] cursor-pointer"
              onClick={() => onRowClick && onRowClick(item)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onRowClick && onRowClick(item);
                }
              }}
            >
              <td><strong>{safeStr(item.transaction_id)}</strong></td>
              <td>{safeStr(item.customer_id)}</td>
              <td>{formatRupees(item.amount)}</td>
              <td><StatusBadge value={item.payment_status} /></td>
              <td><RiskBadge value={item.risk_level} /></td>
              <td className="text-xs text-[#20302C]">{safeStr(item.agent_diagnosis)}</td>
              <td>
                <div className="flex items-center gap-1">
                  <span className="text-[10px] text-[#68746F] uppercase font-bold">AI recommends:</span>
                  <ActionBadge value={item.agent_action || item.recommended_action} />
                </div>
              </td>
              <td className="font-semibold text-[#173F35]">{item.agent_confidence != null ? (safeNum(item.agent_confidence) * 100).toFixed(0) + "%" : "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ExecutionTable({ items, onRowClick }) {
  if (!items || items.length === 0) return <div className="p-8 text-center text-[#68746F]">No records available.</div>;
  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>TRANSACTION</th><th>AI RECOMMENDS</th><th>EXECUTION STATUS</th>
            <th>RECOVERY STATUS</th><th>AMOUNT</th><th>POLICY AUTHORIZATION RESULT</th><th>TIMESTAMP</th>
          </tr>
        </thead>
        <tbody>
          {items.slice(0, 100).map((item, i) => (
            <tr
              key={item.transaction_id || i}
              tabIndex={0}
              className="hover:bg-[#F7F5F0] cursor-pointer"
              onClick={() => onRowClick && onRowClick(item)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onRowClick && onRowClick(item);
                }
              }}
            >
              <td><strong>{safeStr(item.transaction_id)}</strong></td>
              <td>
                <div className="flex items-center gap-1">
                  <span className="text-[10px] text-[#68746F]">AI recommends:</span>
                  <ActionBadge value={item.agent_action} />
                </div>
              </td>
              <td><StatusBadge value={item.execution_status} /></td>
              <td><StatusBadge value={item.recovery_status} /></td>
              <td className="font-semibold text-[#173F35]">{formatRupees(item.amount)}</td>
              <td className="text-xs text-[#68746F]">{safeStr(item.policy_reason || item.execution_message)}</td>
              <td className="text-xs text-[#68746F]">{safeStr(item.executed_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AuditTable({ items }) {
  if (!items || items.length === 0) return <div className="p-8 text-center text-[#68746F]">No records available.</div>;
  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>TRANSACTION</th><th>CUSTOMER</th><th>AI RECOMMENDS</th>
            <th>POLICY AUTHORIZES</th><th>EXECUTION</th><th>RECOVERY</th><th>MESSAGE</th><th>TIMESTAMP</th>
          </tr>
        </thead>
        <tbody>
          {items.slice(0, 100).map((item, i) => (
            <tr key={item.transaction_id || i}>
              <td><strong>{safeStr(item.transaction_id)}</strong></td>
              <td>{safeStr(item.customer_id)}</td>
              <td>
                <div className="flex items-center gap-1">
                  <span className="text-[10px] text-[#68746F]">AI recommends:</span>
                  <ActionBadge value={item.agent_action} />
                </div>
              </td>
              <td>
                <span className={safeStr(item.policy_decision) === "ALLOW" ? "eligible-yes" : "eligible-no"}>
                  Policy authorizes: {safeStr(item.policy_decision)}
                </span>
              </td>
              <td><StatusBadge value={item.execution_status} /></td>
              <td><StatusBadge value={item.recovery_status} /></td>
              <td className="text-xs text-[#68746F]">{safeStr(item.execution_message || item.policy_reason)}</td>
              <td className="text-xs text-[#68746F]">{safeStr(item.executed_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RiskTable({ items, onRowClick }) {
  if (!items || items.length === 0) return <div className="p-8 text-center text-[#68746F]">No records available.</div>;
  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>TRANSACTION</th><th>CUSTOMER</th><th>AMOUNT</th><th>RISK SCORE</th>
            <th>RISK LEVEL</th><th>FAILURE REASON</th><th>ELIGIBLE</th><th>AI RECOMMENDS</th>
          </tr>
        </thead>
        <tbody>
          {items.slice(0, 100).map((item, i) => (
            <tr
              key={item.transaction_id || i}
              tabIndex={0}
              className="hover:bg-[#F7F5F0] cursor-pointer"
              onClick={() => onRowClick && onRowClick(item)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onRowClick && onRowClick(item);
                }
              }}
            >
              <td><strong>{safeStr(item.transaction_id)}</strong></td>
              <td>{safeStr(item.customer_id)}</td>
              <td className="font-semibold text-[#173F35]">{formatRupees(item.amount)}</td>
              <td><strong>{safeStr(item.risk_score)}</strong></td>
              <td><RiskBadge value={item.risk_level} /></td>
              <td>{safeStr(item.failure_reason)}</td>
              <td><EligibleBadge value={item.recovery_eligible} /></td>
              <td>
                <div className="flex items-center gap-1">
                  <span className="text-[10px] text-[#68746F]">AI recommends:</span>
                  <ActionBadge value={item.recommended_action || item.agent_action} />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function App() {
  const [page, setPage] = useState("overview");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dashboard, setDashboard] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [transactions, setTransactions] = useState(null);
  const [decisions, setDecisions] = useState(null);
  const [execution, setExecution] = useState(null);
  const [audit, setAudit] = useState(null);
  const [risk, setRisk] = useState(null);
  const [loading, setLoading] = useState(true);
  const [coreError, setCoreError] = useState("");

  async function loadData() {
    try {
      setLoading(true);
      setCoreError("");
      const [dashboardData, metricsData, transactionsData] = await Promise.all([
        getDashboard(), getMetrics(), getTransactions()
      ]);
      setDashboard(dashboardData);
      setMetrics(metricsData);
      setTransactions(transactionsData);
      await Promise.allSettled([
        getDecisions().then(setDecisions).catch(() => {}),
        getExecution().then(setExecution).catch(() => {}),
        getAudit().then(setAudit).catch(() => {}),
        getRisk().then(setRisk).catch(() => {}),
      ]);
    } catch (err) {
      console.error(err);
      const message = err.message || 'Could not connect to RecoverAI backend.';
      setCoreError(message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadData() }, []);

  // Transaction Detail Drawer State
  const [selectedTx, setSelectedTx] = useState(null);
  const closeDrawer = () => setSelectedTx(null);

  // Escape key listener for detail drawer
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && selectedTx) {
        closeDrawer();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedTx]);

  function renderPage() {
    switch (page) {
      case "overview":
        return <OverviewPage dashboard={dashboard} metrics={metrics} transactions={transactions} />;
      case "transactions":
        return <Section title="Transactions" sub="Payment activity"><TransactionsTable data={transactions} onRowClick={setSelectedTx} /></Section>;
      case "decisions":
        return <Section title="Decision Engine" sub="AI recovery recommendations"><DecisionsTable items={decisions?.items} onRowClick={setSelectedTx} /></Section>;
      case "execution":
        return <Section title="Execution Control Center" sub="Agent-executed actions"><ExecutionTable items={execution?.items} onRowClick={setSelectedTx} /></Section>;
      case "audit":
        return <Section title="Audit Log" sub="Complete activity trail"><AuditTable items={audit?.items} /></Section>;
      case "risk":
        return <Section title="Risk Analysis" sub="Transaction-level risk"><RiskTable items={risk?.items} onRowClick={setSelectedTx} /></Section>;
      case "simulator":
        return <SimulatorView onSimulate={loadData} />;
      case "opportunities":
        return <OpportunitiesPage transactions={transactions} onRowClick={setSelectedTx} />;
      case "policy":
        return <PolicyPage audit={audit} dashboard={dashboard} />;
      default:
        return <OverviewPage dashboard={dashboard} metrics={metrics} transactions={transactions} />;
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F7F5F0] flex items-center justify-center p-4">
        <div className="bg-white p-8 rounded-2xl border border-[#DDE3DF] shadow-md text-center max-w-sm w-full">
          <div className="w-12 h-12 bg-[#2F8F6B] text-white font-black text-2xl rounded-xl flex items-center justify-center mx-auto mb-4">
            R
          </div>
          <h2 className="text-xl font-bold text-[#173F35]">RecoverAI</h2>
          <p className="text-xs text-[#68746F] mt-1 animate-pulse">Loading Revenue Intelligence...</p>
        </div>
      </div>
    );
  }

  if (coreError) {
    return (
      <div className="min-h-screen bg-[#F7F5F0] flex items-center justify-center p-4">
        <div className="bg-white p-8 rounded-2xl border border-[#D96C55]/30 shadow-md text-center max-w-md w-full">
          <h2 className="text-xl font-bold text-[#D96C55]">Connection Error</h2>
          <p className="text-xs text-[#68746F] mt-2 mb-4">{coreError}</p>
          <button
            className="px-4 py-2 bg-[#173F35] text-white rounded-lg font-bold text-sm hover:bg-[#2F8F6B] transition-colors"
            onClick={loadData}
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <ToastProvider>
      <div className="app flex min-h-screen bg-[#F7F5F0] text-[#20302C]">
        <Sidebar
          page={page}
          setPage={setPage}
          mobileOpen={mobileOpen}
          setMobileOpen={setMobileOpen}
        />
        <div className="flex flex-col flex-1 min-w-0">
          <TopBar
            title="RecoverAI Dashboard"
            description="AI Revenue Recovery &amp; Intelligence Platform"
            mobileOpen={mobileOpen}
            setMobileOpen={setMobileOpen}
          />
          <main className="main flex-1 p-4 md:p-6 overflow-x-hidden max-w-full">
            {renderPage()}
          </main>
        </div>

        {/* Transaction Detail Drawer */}
        {selectedTx && (
          <div
            className="fixed inset-0 bg-black/50 z-50 flex justify-end"
            role="dialog"
            aria-modal="true"
            aria-label="Transaction details modal"
            onClick={closeDrawer}
          >
            <div
              className="bg-white w-full max-w-md h-full p-6 overflow-y-auto shadow-2xl flex flex-col justify-between"
              onClick={e => e.stopPropagation()}
              tabIndex={0}
            >
              <div>
                <div className="flex items-center justify-between pb-4 border-b border-[#DDE3DF] mb-4">
                  <h2 className="text-lg font-bold text-[#173F35]">
                    Transaction {selectedTx.transaction_id}
                  </h2>
                  <button
                    className="p-1 rounded text-[#68746F] hover:text-[#20302C] hover:bg-[#F7F5F0]"
                    onClick={closeDrawer}
                    aria-label="Close transaction details"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="bg-[#F7F5F0] p-2.5 rounded-lg">
                      <span className="text-[#68746F] block font-semibold">Customer ID</span>
                      <strong className="text-sm text-[#20302C]">{selectedTx.customer_id}</strong>
                    </div>
                    <div className="bg-[#F7F5F0] p-2.5 rounded-lg">
                      <span className="text-[#68746F] block font-semibold">Amount</span>
                      <strong className="text-sm text-[#173F35]">{formatRupees(selectedTx.amount)}</strong>
                    </div>
                    <div className="bg-[#F7F5F0] p-2.5 rounded-lg">
                      <span className="text-[#68746F] block font-semibold">Payment Status</span>
                      <StatusBadge value={selectedTx.payment_status} />
                    </div>
                    <div className="bg-[#F7F5F0] p-2.5 rounded-lg">
                      <span className="text-[#68746F] block font-semibold">Risk Level</span>
                      <RiskBadge value={selectedTx.risk_level} />
                    </div>
                  </div>

                  <div className="bg-[#E4F1EC] p-3 rounded-lg border border-[#2F8F6B]/30">
                    <span className="text-[11px] font-bold text-[#173F35] block uppercase mb-1">
                      AI Diagnosis &amp; Recommendation
                    </span>
                    <p className="text-xs text-[#20302C] mb-2">
                      <strong>AI recommends:</strong> <ActionBadge value={selectedTx.recommended_action || selectedTx.agent_action || "retry"} />
                    </p>
                    <p className="text-xs text-[#68746F]">
                      {selectedTx.agent_diagnosis || "Analyzed payment telemetry & failure patterns."}
                    </p>
                  </div>

                  <div className="bg-[#F7F5F0] p-3 rounded-lg border border-[#DDE3DF]">
                    <span className="text-[11px] font-bold text-[#76566E] block uppercase mb-1">
                      Policy Authorization &amp; Governance
                    </span>
                    <p className="text-xs text-[#20302C]">
                      <strong>Policy authorizes:</strong> <span className="eligible-yes">ALLOW</span>
                    </p>
                    <p className="text-xs text-[#68746F] mt-1">
                      Bounded execution rules permit 1-click retry dispatch.
                    </p>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-[#DDE3DF] mt-6">
                <button
                  onClick={closeDrawer}
                  className="w-full py-2.5 bg-[#173F35] hover:bg-[#2F8F6B] text-white font-bold rounded-lg text-sm transition-colors"
                >
                  Close Details
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </ToastProvider>
  );
}

export default App;
