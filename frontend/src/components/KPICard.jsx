// src/components/KPICard.jsx
import React, { useEffect, useState } from 'react';
import { useToast } from './ui/ToastProvider';

// Simple count-up animation using requestAnimationFrame
export default function KPICard({ icon, title, value, sub }) {
  const [display, setDisplay] = useState(0);
  const duration = 1200; // ms
  const start = Date.now();

  useEffect(() => {
    let animationFrame;
    const step = () => {
      const now = Date.now();
      const progress = Math.min((now - start) / duration, 1);
      setDisplay(Math.floor(progress * value));
      if (progress < 1) animationFrame = requestAnimationFrame(step);
    };
    step();
    return () => cancelAnimationFrame(animationFrame);
  }, [value]);

  return (
    <div className="card kpi-card p-4 bg-recovery-light border border-border rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200">
      <div className="flex items-center space-x-2">
        <span className="text-2xl font-bold text-forest">{icon}</span>
        <div>
          <h3 className="text-sm font-medium text-text-secondary">{title}</h3>
          <p className="text-xl font-semibold text-text-primary">{display.toLocaleString('en-IN')}</p>
          {sub && <p className="text-xs text-text-secondary">{sub}</p>}
        </div>
      </div>
    </div>
  );
}
