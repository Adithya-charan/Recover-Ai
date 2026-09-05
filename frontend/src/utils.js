// src/utils.js
export function fmt(value) {
  return Number(value || 0).toLocaleString('en-IN');
}

export function formatRupees(value) {
  return '₹' + fmt(value);
}

export function safeStr(v) {
  if (v === null || v === undefined || v === '') return '-';
  return String(v);
}

export function safeNum(v) {
  const n = Number(v);
  return isNaN(n) ? 0 : n;
}

export function isEligible(v) {
  return v === true || safeStr(v).toLowerCase() === "true";
}
