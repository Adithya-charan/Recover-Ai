// src/components/Badges.jsx
import React from 'react';
import { safeStr, isEligible } from '../utils';

export function StatusBadge({ value }) {
  const v = safeStr(value).toLowerCase();
  let cls = "status-badge";
  if (v === "success" || v === "recovered" || v === "simulated_delivered" || v === "simulated_sent") cls += " success";
  else if (v === "failed" || v === "failure") cls += " failed";
  else if (v === "abandoned" || v === "follow_up") cls += " abandoned";
  else if (v === "executed" || v === "simulated") cls += " executed";
  else if (v === "blocked") cls += " blocked";
  return <span className={cls}>{safeStr(value)}</span>;
}

export function RiskBadge({ value }) {
  const v = safeStr(value).toLowerCase();
  return <span className={"risk-badge " + (v || "low")}>{safeStr(value) || "low"}</span>;
}

export function ActionBadge({ value }) {
  return <span className="action-badge">{safeStr(value)}</span>;
}

export function EligibleBadge({ value }) {
  return <span className={isEligible(value) ? "eligible-yes" : "eligible-no"}>{isEligible(value) ? "Yes" : "No"}</span>;
}
