// src/components/OpportunitiesCarousel.jsx
import React from 'react';
import { formatRupees } from '../utils';
import { RiskBadge, ActionBadge } from '../components/Badges';

export default function OpportunitiesCarousel({ transactions }) {
  const items = (transactions?.items || []).filter(tx => tx.recovery_eligible).slice(0, 6);

  return (
    <div className="flex overflow-x-auto gap-4 py-2 scrollbar-thin">
      {items.length > 0 ? (
        items.map((tx) => (
          <div
            key={tx.transaction_id}
            className="min-w-[220px] bg-[#E4F1EC] p-4 rounded-xl border border-[#2F8F6B]/30 shadow-2xs flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-sm text-[#173F35]">{tx.transaction_id}</span>
                <RiskBadge value={tx.risk_level} />
              </div>
              <p className="text-xs text-[#68746F] mb-1">Customer: {tx.customer_id}</p>
              <p className="text-base font-extrabold text-[#173F35] mb-2">{formatRupees(tx.amount)}</p>
            </div>
            <div className="pt-2 border-t border-[#DDE3DF] flex items-center justify-between text-[11px]">
              <span className="text-[#68746F] font-semibold">AI recommends:</span>
              <ActionBadge value={tx.recommended_action || tx.agent_action || "retry"} />
            </div>
          </div>
        ))
      ) : (
        <p className="text-xs text-[#68746F] py-4">No eligible recovery candidates at this time.</p>
      )}
    </div>
  );
}
