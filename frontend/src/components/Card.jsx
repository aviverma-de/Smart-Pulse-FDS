import React from 'react';

export default function Card({ children, className = '', glow = false, title, subtitle, action }) {
  return (
    <div
      className={`glass-panel rounded-2xl p-6 transition-all duration-300 relative ${
        glow ? 'border-teal-500/30 shadow-lg shadow-teal-500/10' : 'hover:border-white/15'
      } ${className}`}
    >
      {(title || subtitle || action) && (
        <div className="flex items-start justify-between gap-4 mb-5 pb-4 border-b border-white/5">
          <div>
            {title && <h3 className="text-base font-semibold text-white tracking-tight">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
