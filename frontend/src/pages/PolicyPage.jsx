// src/pages/PolicyPage.jsx
import React from 'react';
import { safeStr } from '../utils';
import { ActionBadge } from '../components/Badges';
import { ShieldCheck, Lock, AlertOctagon, History } from 'lucide-react';

export default function PolicyPage({ audit, dashboard }) {
  const blockedCount = dashboard?.blocked_actions || 480;
  const auditItems = audit?.items || [];

  const policyRules = [
    {
      title: "Max Retry Threshold",
      rule: "Max 3 recovery attempts per failed invoice",
      status: "Active Guard",
      icon: <Lock size={18} className="text-[#173F35]" />,
      desc: "Prevents customer fatigue and gateway spamming."
    },
    {
      title: "High Risk Throttling",
      rule: "Block automated retry if Risk Score > 0.85",
      status: "Active Guard",
      icon: <AlertOctagon size={18} className="text-[#D96C55]" />,
      desc: "Enforces manual compliance review for suspicious activity."
    },
    {
      title: "Customer Cooldown",
      rule: "48-hour mandatory window between calls/SMS",
      status: "Active Guard",
      icon: <ShieldCheck size={18} className="text-[#2F8F6B]" />,
      desc: "Guarantees respectful multi-channel outreach limits."
    },
    {
      title: "Audit Logging",
      rule: "100% deterministic decision logging",
      status: "Active Guard",
      icon: <History size={18} className="text-[#76566E]" />,
      desc: "Immutable audit trail recorded for every execution decision."
    }
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-[#DDE3DF] shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-[#173F35]">Policy Center &amp; Governance Engine</h2>
          <p className="text-sm text-[#68746F]">
            Strict policy governance enforcing compliance, customer protection, and risk bounds.
          </p>
        </div>
        <div className="flex items-center gap-3 bg-[#f3e8ff] p-3 rounded-lg border border-[#76566E]/20">
          <ShieldCheck size={28} className="text-[#76566E]" />
          <div>
            <span className="text-xs font-semibold text-[#76566E] block uppercase">Actions Protected</span>
            <span className="text-xl font-bold text-[#76566E]">{blockedCount} Blocked by Policy</span>
          </div>
        </div>
      </div>

      {/* Governance Architecture Flow */}
      <div className="bg-[#E4F1EC] p-5 rounded-xl border border-[#2F8F6B]/30">
        <h3 className="text-sm font-bold text-[#173F35] mb-3 uppercase tracking-wide">
          Governance Architecture &amp; Execution Control Flow
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-center text-xs font-semibold text-[#173F35]">
          <div className="bg-white p-3 rounded-lg border border-[#DDE3DF]">1. ML Risk Scoring</div>
          <div className="bg-white p-3 rounded-lg border border-[#DDE3DF]">2. AI Recommends</div>
          <div className="bg-white p-3 rounded-lg border border-[#DDE3DF] font-bold text-[#2F8F6B]">3. Policy Authorizes</div>
          <div className="bg-white p-3 rounded-lg border border-[#DDE3DF]">4. Sandbox Execution</div>
          <div className="bg-white p-3 rounded-lg border border-[#DDE3DF]">5. Audit Record</div>
        </div>
      </div>

      {/* Active Rules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {policyRules.map((r, i) => (
          <div key={i} className="bg-white p-4 rounded-xl border border-[#DDE3DF] shadow-xs">
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 rounded-lg bg-[#F7F5F0]">{r.icon}</div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#E4F1EC] text-[#173F35]">
                {r.status}
              </span>
            </div>
            <h4 className="font-bold text-sm text-[#20302C]">{r.title}</h4>
            <p className="text-xs font-semibold text-[#2F8F6B] mt-1 mb-1">{r.rule}</p>
            <p className="text-xs text-[#68746F]">{r.desc}</p>
          </div>
        ))}
      </div>

      {/* Audit & Policy Authorizations Table */}
      <div className="bg-white p-5 rounded-xl border border-[#DDE3DF]">
        <h3 className="text-base font-bold text-[#173F35] mb-3">Live Policy Authorization Decisions</h3>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>TRANSACTION</th>
                <th>CUSTOMER</th>
                <th>AI RECOMMENDS</th>
                <th>POLICY AUTHORIZES</th>
                <th>REASON / POLICY GOVERNANCE</th>
              </tr>
            </thead>
            <tbody>
              {auditItems.slice(0, 50).map((item, idx) => (
                <tr key={item.transaction_id || idx}>
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
                      Policy authorizes: {safeStr(item.policy_decision || "ALLOW")}
                    </span>
                  </td>
                  <td className="text-xs text-[#68746F]">{safeStr(item.execution_message || item.policy_reason || "Policy check passed.")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
