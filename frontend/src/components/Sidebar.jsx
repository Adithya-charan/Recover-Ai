// src/components/Sidebar.jsx
import React, { useEffect } from "react";
import { Home, LayoutList, Bot, Zap, Activity, BarChart, FileText, Shield, X, Play } from "lucide-react";

export default function Sidebar({ page, setPage, mobileOpen, setMobileOpen }) {
  // Handle Escape key to close mobile sidebar
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && mobileOpen) {
        setMobileOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mobileOpen, setMobileOpen]);

  const handleNavClick = (targetPage) => {
    setPage(targetPage);
    if (setMobileOpen) {
      setMobileOpen(false);
    }
  };

  const navContent = (
    <>
      <div className="brand flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="brand-logo">R</div>
          <div>
            <div className="brand-name font-bold text-white text-base leading-tight">RecoverAI</div>
            <div className="brand-subtitle text-xs text-[#A3BFB7]">Revenue Intelligence</div>
          </div>
        </div>
        {mobileOpen && (
          <button
            onClick={() => setMobileOpen(false)}
            className="md:hidden text-[#A3BFB7] hover:text-white p-1 rounded"
            aria-label="Close navigation menu"
          >
            <X size={20} />
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        <div className="nav-section">
          <h3 className="nav-heading">INTELLIGENCE</h3>
          <button
            className={"nav-button" + (page === "overview" ? " active" : "")}
            onClick={() => handleNavClick("overview")}
          >
            <span className="nav-icon"><Home size={16} /></span> Overview
          </button>
          <button
            className={"nav-button" + (page === "transactions" ? " active" : "")}
            onClick={() => handleNavClick("transactions")}
          >
            <span className="nav-icon"><LayoutList size={16} /></span> Transactions
          </button>
          <button
            className={"nav-button" + (page === "decisions" ? " active" : "")}
            onClick={() => handleNavClick("decisions")}
          >
            <span className="nav-icon"><Bot size={16} /></span> AI Decisions
          </button>
          <button
            className={"nav-button" + (page === "risk" ? " active" : "")}
            onClick={() => handleNavClick("risk")}
          >
            <span className="nav-icon"><Activity size={16} /></span> Risk Analysis
          </button>
          <button
            className={"nav-button" + (page === "simulator" ? " active" : "")}
            onClick={() => handleNavClick("simulator")}
          >
            <span className="nav-icon"><Play size={16} /></span> Pipeline Simulator
          </button>
        </div>

        <div className="nav-section">
          <h3 className="nav-heading">GOVERNANCE</h3>
          <button
            className={"nav-button" + (page === "opportunities" ? " active" : "")}
            onClick={() => handleNavClick("opportunities")}
          >
            <span className="nav-icon"><BarChart size={16} /></span> Recovery Opportunities
          </button>
          <button
            className={"nav-button" + (page === "policy" ? " active" : "")}
            onClick={() => handleNavClick("policy")}
          >
            <span className="nav-icon"><Shield size={16} /></span> Policy Center
          </button>
          <button
            className={"nav-button" + (page === "execution" ? " active" : "")}
            onClick={() => handleNavClick("execution")}
          >
            <span className="nav-icon"><Zap size={16} /></span> Execution
          </button>
          <button
            className={"nav-button" + (page === "audit" ? " active" : "")}
            onClick={() => handleNavClick("audit")}
          >
            <span className="nav-icon"><FileText size={16} /></span> Audit Log
          </button>
        </div>
      </div>

      <div className="sidebar-bottom p-4 border-t border-white/10 text-xs text-[#A3BFB7]">
        <div className="system-status flex items-center gap-2 mb-2">
          <span className="w-2 h-2 rounded-full bg-[#2F8F6B] animate-pulse"></span>
          <div>
            <strong className="text-white block">System Online</strong>
            <span className="text-[11px]">All services operational</span>
          </div>
        </div>
        <div className="version text-[10px] text-white/50">RecoverAI v1.0.0</div>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="sidebar hidden md:flex">
        {navContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-50 md:hidden flex"
          onClick={() => setMobileOpen(false)}
          role="dialog"
          aria-modal="true"
          aria-label="Navigation drawer"
        >
          <aside
            className="sidebar w-72 h-full flex flex-col shadow-2xl bg-[#173F35]"
            onClick={(e) => e.stopPropagation()}
          >
            {navContent}
          </aside>
        </div>
      )}
    </>
  );
}
