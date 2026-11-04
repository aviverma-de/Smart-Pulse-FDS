import React from 'react';
import { useCountUp } from '../hooks/useCountUp';

export default function StatCard({
  title,
  value,
  decimals = 0,
  prefix = '',
  suffix = '',
  subtitle,
  icon: Icon,
  trend,
  color = 'teal',
}) {
  const numericValue = typeof value === 'number' ? value : parseFloat(value) || 0;
  const animatedNumber = useCountUp(numericValue, 1100, decimals);

  const colorStyles = {
    teal: 'border-teal-500/20 text-teal-400 bg-teal-500/10 shadow-teal-500/10',
    cyan: 'border-cyan-500/20 text-cyan-400 bg-cyan-500/10 shadow-cyan-500/10',
    rose: 'border-rose-500/20 text-rose-400 bg-rose-500/10 shadow-rose-500/10',
    amber: 'border-amber-500/20 text-amber-400 bg-amber-500/10 shadow-amber-500/10',
    indigo: 'border-indigo-500/20 text-indigo-400 bg-indigo-500/10 shadow-indigo-500/10',
  };

  return (
    <div className="glass-panel glass-panel-hover rounded-2xl p-5 border border-white/10 relative overflow-hidden group">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-slate-400 tracking-wider uppercase">
          {title}
        </span>
        {Icon && (
          <div className={`p-2 rounded-xl border ${colorStyles[color]} transition-transform group-hover:scale-110`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-1">
        {prefix && <span className="text-xl font-bold text-slate-300">{prefix}</span>}
        <span className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          {animatedNumber}
        </span>
        {suffix && <span className="text-sm font-semibold text-teal-300 ml-1">{suffix}</span>}
      </div>

      {subtitle && (
        <p className="text-xs text-slate-400 mt-2 flex items-center gap-1.5">
          {trend && <span className="font-semibold text-teal-300">{trend}</span>}
          <span>{subtitle}</span>
        </p>
      )}
    </div>
  );
}
