// src/pages/OverviewPage.jsx
import React from 'react';
import KPICard from '../components/KPICard';
import PipelineViz from '../components/PipelineViz';
import OpportunitiesCarousel from '../components/OpportunitiesCarousel';
import CommandCenter from '../components/CommandCenter';
import RazorpayCard from '../components/RazorpayCard';

export default function OverviewPage({ dashboard, metrics, transactions }) {
  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <section className="bg-[#E4F1EC] p-6 md:p-8 rounded-xl border border-[#2F8F6B]/30 shadow-xs">
        <h1 className="text-2xl md:text-3xl font-bold text-[#173F35]">AI Revenue Recovery &amp; Intelligence</h1>
        <p className="mt-2 text-sm text-[#68746F] max-w-2xl">
          Real-time monitoring for failed payments, ML risk signals, AI recovery recommendations, and policy-governed execution.
        </p>
      </section>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          icon="💰"
          title="Revenue at Risk"
          value={dashboard?.revenue_at_risk || 0}
          sub={`${dashboard?.recovery_eligible || 0} eligible for AI recovery`}
        />
        <KPICard
          icon="✅"
          title="Recovered Revenue"
          value={dashboard?.recovered_amount || 0}
          sub={`${metrics?.successful_recoveries || 0} successful recoveries`}
        />
        <KPICard
          icon="⚡"
          title="Recovery Attempts"
          value={dashboard?.recovery_attempts || 0}
          sub={`${metrics?.attempt_success_rate || 0}% AI success rate`}
        />
        <KPICard
          icon="🚫"
          title="Policy Blocked"
          value={dashboard?.blocked_actions || 0}
          sub="Protected by Policy Engine"
        />
      </div>

      {/* Pipeline Visualization */}
      <PipelineViz dashboard={dashboard} metrics={metrics} />

      {/* Opportunities Carousel */}
      <section className="bg-white p-5 rounded-xl border border-[#DDE3DF] shadow-xs">
        <h2 className="text-lg font-bold text-[#173F35] mb-3">High-Priority Recovery Candidates</h2>
        <OpportunitiesCarousel transactions={transactions} />
      </section>

      {/* Razorpay Integration Card */}
      <section>
        <RazorpayCard />
      </section>

      {/* Command Center */}
      <section>
        <CommandCenter />
      </section>
    </div>
  );
}
