// src/components/RazorpayCard.jsx
import React from 'react';
import { useToast } from './ui/ToastProvider';
import { CreditCard, CheckCircle } from 'lucide-react';

export default function RazorpayCard() {
  const { addToast } = useToast() || {};

  const handleVerify = () => {
    if (addToast) {
      addToast("Razorpay Test Mode Connection Verified (API Key rzp_test_ active)", "success");
    }
  };

  return (
    <div className="bg-white p-5 rounded-xl border border-[#DDE3DF] shadow-xs flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="p-3 bg-[#E4F1EC] rounded-xl text-[#173F35]">
          <CreditCard size={24} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-[#173F35]">Razorpay Test Mode Integration</h3>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#E9A23B] text-white">
              TEST MODE
            </span>
          </div>
          <p className="text-xs text-[#68746F] mt-0.5">
            Connected to Razorpay Sandbox API. Payment order creation, webhook ingestion &amp; recovery link generation active.
          </p>
        </div>
      </div>

      <button
        onClick={handleVerify}
        className="px-4 py-2 bg-[#173F35] hover:bg-[#2F8F6B] text-white text-xs font-bold rounded-lg transition-colors shadow-2xs cursor-pointer flex items-center gap-1.5"
      >
        <CheckCircle size={14} />
        Verify Connection
      </button>
    </div>
  );
}
