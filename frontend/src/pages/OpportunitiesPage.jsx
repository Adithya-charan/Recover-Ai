// src/pages/OpportunitiesPage.jsx
import React, { useState } from 'react';
import { formatRupees, safeStr, isEligible } from '../utils';
import { StatusBadge, RiskBadge, ActionBadge } from '../components/Badges';

export default function OpportunitiesPage({ transactions, onRowClick }) {
  const [minAmount, setMinAmount] = useState(0);
  const [selectedRisk, setSelectedRisk] = useState("all");

  const items = (transactions?.items || []).filter(item => isEligible(item.recovery_eligible));

  let filtered = items;
  if (minAmount > 0) {
    filtered = filtered.filter(i => Number(i.amount) >= minAmount);
  }
  if (selectedRisk !== "all") {
    filtered = filtered.filter(i => safeStr(i.risk_level).toLowerCase() === selectedRisk);
  }

  const totalAtRisk = filtered.reduce((acc, curr) => acc + Number(curr.amount || 0), 0);

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-[#DDE3DF] shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-[#173F35]">Recovery Opportunities</h2>
          <p className="text-sm text-[#68746F]">
            High-intent failed payments prioritized for automated AI recovery dispatch
          </p>
        </div>
        <div className="flex items-center gap-4 bg-[#E7F5EF] p-3 rounded-lg border border-[#2F8F6B]/20">
          <div>
            <span className="text-xs font-semibold text-[#68746F] block">Eligible Potential</span>
            <span className="text-xl font-bold text-[#2F8F6B]">{formatRupees(totalAtRisk)}</span>
          </div>
          <div className="h-8 w-px bg-[#DDE3DF]"></div>
          <div>
            <span className="text-xs font-semibold text-[#68746F] block">Opportunities</span>
            <span className="text-xl font-bold text-[#173F35]">{filtered.length}</span>
          </div>
        </div>
      </div>

      <div className="filters">
        <select
          className="filter-select"
          value={minAmount}
          onChange={e => setMinAmount(Number(e.target.value))}
        >
          <option value={0}>All Amounts</option>
          <option value={1000}>Min ₹1,000</option>
          <option value={2500}>Min ₹2,500</option>
          <option value={5000}>Min ₹5,000</option>
        </select>

        <select
          className="filter-select"
          value={selectedRisk}
          onChange={e => setSelectedRisk(e.target.value)}
        >
          <option value="all">All Risk Levels</option>
          <option value="low">Low Risk Only</option>
          <option value="medium">Medium Risk</option>
          <option value="high">High Risk</option>
        </select>

        <span className="filter-count text-xs font-semibold text-[#68746F]">
          Showing {filtered.length} eligible recovery candidates
        </span>
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>TRANSACTION</th>
              <th>CUSTOMER</th>
              <th>AMOUNT</th>
              <th>STATUS</th>
              <th>FAILURE REASON</th>
              <th>RISK LEVEL</th>
              <th>AI RECOMMENDS</th>
            </tr>
          </thead>
          <tbody>
            {filtered.slice(0, 100).map((item, idx) => (
              <tr
                key={item.transaction_id || idx}
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
                <td><RiskBadge value={item.risk_level} /></td>
                <td>
                  <div className="flex items-center gap-1">
                    <span className="text-[10px] text-[#68746F] uppercase font-bold">AI recommends:</span>
                    <ActionBadge value={item.recommended_action || item.agent_action || "retry"} />
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
