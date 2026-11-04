import React from 'react';

export default function RiskBadge({ category, size = 'md' }) {
  const isHigh = category === 'High Risk' || category === 'High' || category === 1;

  const sizeClasses = {
    sm: 'px-2.5 py-0.5 text-xs',
    md: 'px-3.5 py-1 text-sm font-semibold',
    lg: 'px-5 py-2 text-base font-bold',
  };

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border shadow-sm transition-all ${
        sizeClasses[size]
      } ${
        isHigh
          ? 'bg-rose-500/15 border-rose-500/40 text-rose-300 shadow-rose-500/10'
          : 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300 shadow-emerald-500/10'
      }`}
    >
      <span
        className={`w-2 h-2 rounded-full animate-pulse ${
          isHigh ? 'bg-rose-400' : 'bg-emerald-400'
        }`}
      />
      <span>{isHigh ? 'High Burnout Risk' : 'Low / Baseline Risk'}</span>
    </span>
  );
}
