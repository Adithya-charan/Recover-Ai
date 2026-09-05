// src/components/SimulatorView.jsx
import React, { useState } from 'react';
import { formatRupees, safeNum } from '../utils';

export default function SimulatorView({ onSimulate }) {
  const [txId, setTxId] = useState("TX_ORCH_99");
  const [custId, setCustId] = useState("CUST1099");
  const [amount, setAmount] = useState(1999);
  const [status, setStatus] = useState("failed");
  const [reason, setReason] = useState("timeout");
  const [attempts, setAttempts] = useState(1);
  const [prevPayments, setPrevPayments] = useState(4);
  const [prevFailures, setPrevFailures] = useState(1);
  const [days, setDays] = useState(2);
  const [subStatus, setSubStatus] = useState("active");
  const [loading, setLoading] = useState(false);
  const [orchestration, setOrchestration] = useState(null);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setOrchestration(null);
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
    };
    try {
      const res = await fetch("http://127.0.0.1:8000/api/recovery/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Orchestration API failed");
      const data = await res.json();
      setOrchestration(data);
      if (onSimulate) onSimulate();
    } catch (err) {
      setError(err.message || "Failed to run recovery simulation.");
    } finally {
      setLoading(false);
    }
  }

  const pRes = orchestration?.pipeline_result;

  return (
    <section className="bg-white p-6 rounded-xl border border-[#DDE3DF] shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-6 pb-4 border-b border-[#DDE3DF]">
        <div>
          <h2 className="text-2xl font-bold text-[#173F35]">Unified Multi-Channel Pipeline Simulator</h2>
          <p className="text-sm text-[#68746F]">
            Test real-time ML risk scoring, LLM diagnosis, policy governance, payment sandbox &amp; multi-channel dispatch.
          </p>
        </div>
        <span className="text-xs font-bold px-3 py-1 rounded bg-[#E7F5EF] text-[#2F8F6B] border border-[#2F8F6B]/20">
          SIMULATION MODE
        </span>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-xs font-semibold text-[#68746F] mb-1">Transaction ID</label>
          <input className="filter-input w-full" type="text" value={txId} onChange={e => setTxId(e.target.value)} required />
        </div>
        <div>
          <label className="block text-xs font-semibold text-[#68746F] mb-1">Customer ID</label>
          <input className="filter-input w-full" type="text" value={custId} onChange={e => setCustId(e.target.value)} required />
        </div>
        <div>
          <label className="block text-xs font-semibold text-[#68746F] mb-1">Amount (₹)</label>
          <input className="filter-input w-full" type="number" value={amount} onChange={e => setAmount(e.target.value)} required />
        </div>
        <div>
          <label className="block text-xs font-semibold text-[#68746F] mb-1">Payment Status</label>
          <select className="filter-select w-full" value={status} onChange={e => setStatus(e.target.value)}>
            <option value="failed">failed</option>
            <option value="abandoned">abandoned</option>
            <option value="success">success</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-[#68746F] mb-1">Failure Reason</label>
          <select className="filter-select w-full" value={reason} onChange={e => setReason(e.target.value)}>
            <option value="timeout">timeout</option>
            <option value="network_error">network_error</option>
            <option value="upi_failure">upi_failure</option>
            <option value="bank_declined">bank_declined</option>
            <option value="insufficient_funds">insufficient_funds</option>
            <option value="authentication_failed">authentication_failed</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-[#68746F] mb-1">Attempt Count</label>
          <input className="filter-input w-full" type="number" value={attempts} onChange={e => setAttempts(e.target.value)} required />
        </div>
        <div>
          <label className="block text-xs font-semibold text-[#68746F] mb-1">Previous Successes</label>
          <input className="filter-input w-full" type="number" value={prevPayments} onChange={e => setPrevPayments(e.target.value)} required />
        </div>
        <div>
          <label className="block text-xs font-semibold text-[#68746F] mb-1">Previous Failures</label>
          <input className="filter-input w-full" type="number" value={prevFailures} onChange={e => setPrevFailures(e.target.value)} required />
        </div>
        <div>
          <label className="block text-xs font-semibold text-[#68746F] mb-1">Days Since Event</label>
          <input className="filter-input w-full" type="number" value={days} onChange={e => setDays(e.target.value)} required />
        </div>
        <div className="sm:col-span-2 lg:col-span-3 mt-2">
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-[#173F35] hover:bg-[#2F8F6B] text-white font-bold rounded-lg transition-colors text-sm shadow-xs cursor-pointer"
          >
            {loading ? "Running Complete Recovery Orchestrator..." : "⚡ Run Unified Pipeline Execution"}
          </button>
        </div>
      </form>

      {error && (
        <div className="p-4 bg-[#FBEAE6] text-[#D96C55] rounded-lg border border-[#D96C55]/30 mb-6 text-sm">
          {error}
        </div>
      )}

      {orchestration && (
        <div className="mt-8 pt-6 border-t border-[#DDE3DF]">
          <h3 className="text-lg font-bold text-[#173F35] mb-4">Pipeline Execution Results</h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
            <div className="p-3 bg-[#F7F5F0] rounded-lg border border-[#DDE3DF]">
              <span className="text-[11px] text-[#68746F] block">1. Eligibility</span>
              <strong className="text-sm font-bold text-[#173F35]">{pRes?.eligibility?.eligible ? "Eligible" : "Ineligible"}</strong>
            </div>
            <div className="p-3 bg-[#F7F5F0] rounded-lg border border-[#DDE3DF]">
              <span className="text-[11px] text-[#68746F] block">2. ML Risk</span>
              <strong className="text-sm font-bold text-[#173F35]">{pRes?.risk?.risk_score} ({pRes?.risk?.risk_level})</strong>
            </div>
            <div className="p-3 bg-[#F7F5F0] rounded-lg border border-[#DDE3DF]">
              <span className="text-[11px] text-[#68746F] block">3. AI Recommends</span>
              <strong className="text-sm font-bold text-[#2F8F6B]">{pRes?.decision?.action}</strong>
            </div>
            <div className="p-3 bg-[#F7F5F0] rounded-lg border border-[#DDE3DF]">
              <span className="text-[11px] text-[#68746F] block">4. Policy Authorizes</span>
              <strong className={`text-sm font-bold ${pRes?.policy?.allowed ? "text-[#2F8F6B]" : "text-[#D96C55]"}`}>
                {pRes?.policy?.policy_status}
              </strong>
            </div>
            <div className="p-3 bg-[#F7F5F0] rounded-lg border border-[#DDE3DF]">
              <span className="text-[11px] text-[#68746F] block">5. Recovery Result</span>
              <strong className="text-sm font-bold text-[#173F35]">{pRes?.execution?.recovery_status}</strong>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-white rounded-lg border border-[#DDE3DF]">
              <h4 className="font-bold text-sm text-[#173F35] mb-2">🤖 AI Diagnosis &amp; Policy Governance</h4>
              <p className="text-xs text-[#20302C] mb-1">
                <strong>ML Prob:</strong> {(safeNum(orchestration?.ml_insights?.recovery_probability) * 100).toFixed(1)}% | <strong>Expected Value:</strong> {formatRupees(orchestration?.ml_insights?.expected_recovery_value)}
              </p>
              <p className="text-xs text-[#20302C] mb-1"><strong>AI recommends:</strong> {pRes?.decision?.action} ({pRes?.decision?.diagnosis})</p>
              <p className="text-xs text-[#68746F] mb-1"><strong>Reason:</strong> {pRes?.decision?.reason}</p>
              <p className="text-xs font-semibold text-[#173F35]"><strong>Policy authorizes:</strong> {pRes?.policy?.reason}</p>
            </div>
            <div className="p-4 bg-white rounded-lg border border-[#DDE3DF]">
              <h4 className="font-bold text-sm text-[#173F35] mb-2">📡 Multi-Channel Communications</h4>
              {orchestration?.communications && orchestration.communications.length > 0 ? (
                <div className="space-y-2">
                  {orchestration.communications.map((c, idx) => (
                    <div key={idx} className="p-2 bg-[#F7F5F0] rounded flex items-center justify-between text-xs">
                      <div>
                        <strong className="uppercase text-[10px] text-[#68746F] block">{c.channel}</strong>
                        <span className="text-[#20302C]">{c.delivery_message}</span>
                      </div>
                      <span className="font-bold text-[#2F8F6B] text-[11px]">{c.status}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-[#68746F]">No communications dispatched (Policy Blocked or Ineligible).</p>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
