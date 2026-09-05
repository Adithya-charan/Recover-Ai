// src/components/PipelineViz.jsx
import React from 'react';
import { formatRupees, safeNum } from '../utils';
import { ArrowRight, AlertTriangle, ShieldCheck, Zap, RefreshCw, CheckCircle } from 'lucide-react';

export default function PipelineViz({ dashboard, metrics }) {
  const atRisk = dashboard?.revenue_at_risk || 0;
  const eligibleCount = dashboard?.recovery_eligible || 0;
  const attempts = dashboard?.recovery_attempts || 0;
  const blocked = dashboard?.blocked_actions || 0;
  const recovered = dashboard?.recovered_amount || 0;
  const successRate = metrics?.attempt_success_rate || 0;

  const stages = [
    {
      name: "1. Revenue Risk",
      value: formatRupees(atRisk),
      sub: "Total Failed Volume",
      icon: <AlertTriangle size={18} className="text-[#D96C55]" />,
      badge: "Inbound",
      color: "border-[#D96C55]"
    },
    {
      name: "2. ML Risk & Eligibility",
      value: `${eligibleCount} Transactions`,
      sub: "Eligible for Recovery",
      icon: <ShieldCheck size={18} className="text-[#E9A23B]" />,
      badge: "ML Scored",
      color: "border-[#E9A23B]"
    },
    {
      name: "3. AI Recommendation",
      value: `${attempts} Triggered`,
      sub: `${successRate}% Success Rate`,
      icon: <Zap size={18} className="text-[#173F35]" />,
      badge: "AI Decision",
      color: "border-[#173F35]"
    },
    {
      name: "4. Policy Governance",
      value: `${blocked} Protected`,
      sub: "Policy Enforced",
      icon: <RefreshCw size={18} className="text-[#76566E]" />,
      badge: "Authorized",
      color: "border-[#76566E]"
    },
    {
      name: "5. Recovered Revenue",
      value: formatRupees(recovered),
      sub: `${metrics?.successful_recoveries || 0} Recovered`,
      icon: <CheckCircle size={18} className="text-[#2F8F6B]" />,
      badge: "Complete",
      color: "border-[#2F8F6B]"
    }
  ];

  return (
    <section className="mt-8">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-[#173F35]">End-to-End Recovery Pipeline</h2>
          <p className="text-xs text-[#68746F]">Real-time transformation from failed payment to AI governance &amp; recovered revenue</p>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded bg-[#E4F1EC] text-[#173F35]">
          LIVE BACKEND DATA
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {stages.map((stage, idx) => (
          <div
            key={idx}
            className={`bg-white p-4 rounded-xl border-l-4 ${stage.color} border border-[#DDE3DF] shadow-xs flex flex-col justify-between`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="p-1.5 rounded-lg bg-[#F7F5F0]">{stage.icon}</span>
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#68746F] bg-[#F7F5F0] px-2 py-0.5 rounded">
                {stage.badge}
              </span>
            </div>
            <div>
              <div className="text-xs font-semibold text-[#68746F] mb-1">{stage.name}</div>
              <div className="text-lg font-bold text-[#20302C]">{stage.value}</div>
              <div className="text-xs text-[#68746F] mt-1">{stage.sub}</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
