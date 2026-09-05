// src/components/CommandCenter.jsx
import React from 'react';
import { Phone, MessageSquare, Mail, Smartphone, ShieldCheck, Play } from 'lucide-react';

export default function CommandCenter() {
  const channels = [
    {
      name: "Voice AI Agent",
      type: "Interactive Voice Recovery",
      icon: <Phone size={20} className="text-[#173F35]" />,
      status: "Simulated Active",
      badgeClass: "bg-[#E4F1EC] text-[#173F35]",
      description: "Automated IVR call outbound retry with voice verification & UPI link SMS dispatch."
    },
    {
      name: "WhatsApp Interactive",
      type: "Instant Messaging Channel",
      icon: <MessageSquare size={20} className="text-[#2F8F6B]" />,
      status: "Simulated Sent",
      badgeClass: "bg-[#E7F5EF] text-[#2F8F6B]",
      description: "Delivers 1-click Razorpay payment link directly to customer WhatsApp chat."
    },
    {
      name: "Email Recovery Journey",
      type: "Transactional Email",
      icon: <Mail size={20} className="text-[#E9A23B]" />,
      status: "Simulated Delivered",
      badgeClass: "bg-[#fef3c7] text-[#d97706]",
      description: "Smart email reminder sent with failure diagnosis & alternative payment options."
    },
    {
      name: "SMS Gateway",
      type: "Priority Fallback SMS",
      icon: <Smartphone size={20} className="text-[#76566E]" />,
      status: "Enforced",
      badgeClass: "bg-[#f3e8ff] text-[#76566E]",
      description: "High-priority fallback SMS containing secure Razorpay Checkout shortlink."
    }
  ];

  return (
    <div className="bg-white p-5 rounded-xl border border-[#DDE3DF] shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4 pb-3 border-b border-[#DDE3DF]">
        <div className="flex items-center gap-2">
          <ShieldCheck size={20} className="text-[#2F8F6B]" />
          <div>
            <h3 className="text-base font-bold text-[#173F35]">Multi-Channel Communication Control</h3>
            <p className="text-xs text-[#68746F]">Agent-orchestrated outbound communication dispatch channels</p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded bg-[#E7F5EF] text-[#2F8F6B] border border-[#2F8F6B]/20">
          SIMULATION ENVIRONMENT
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {channels.map((ch, idx) => (
          <div key={idx} className="bg-[#F7F5F0] p-4 rounded-lg border border-[#DDE3DF] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 rounded-lg bg-white shadow-2xs">{ch.icon}</div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${ch.badgeClass}`}>
                  {ch.status}
                </span>
              </div>
              <h4 className="font-bold text-sm text-[#20302C]">{ch.name}</h4>
              <p className="text-[11px] text-[#68746F] mb-2">{ch.type}</p>
              <p className="text-xs text-[#68746F] leading-relaxed">{ch.description}</p>
            </div>
            <div className="mt-3 pt-2 border-t border-[#DDE3DF] flex items-center justify-between text-[11px] text-[#68746F]">
              <span>Governance Check</span>
              <span className="font-semibold text-[#2F8F6B]">ALLOW</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
