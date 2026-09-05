// src/components/TopBar.jsx
import React from "react";
import { Menu } from "lucide-react";

export default function TopBar({ title, description, mobileOpen, setMobileOpen }) {
  return (
    <header className="topbar p-4 bg-white border-b border-[#DDE3DF] shadow-xs flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-3">
        {/* Mobile Hamburger Button */}
        <button
          onClick={() => setMobileOpen && setMobileOpen(!mobileOpen)}
          className="md:hidden p-2 rounded-lg text-[#173F35] hover:bg-[#E4F1EC] transition-colors"
          aria-label="Open navigation menu"
          aria-expanded={mobileOpen}
        >
          <Menu size={22} />
        </button>

        <div>
          <h1 className="text-xl md:text-2xl font-bold text-[#20302C] leading-tight">{title}</h1>
          {description && <p className="text-xs md:text-sm text-[#68746F]">{description}</p>}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="bg-[#E9A23B] text-white px-2.5 py-1 rounded-md font-semibold tracking-wide">
          RAZORPAY — TEST MODE
        </span>
        <span className="bg-[#E7F5EF] text-[#2F8F6B] border border-[#2F8F6B]/20 px-2.5 py-1 rounded-md font-semibold tracking-wide">
          SIMULATION ENVIRONMENT
        </span>
      </div>
    </header>
  );
}
