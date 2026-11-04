import React from 'react';

export default function Gauge({
  value,
  min = 5,
  max = 25,
  label = 'Burnout Score',
  subtitle = '5 to 25 Scale',
}) {
  const percentage = Math.min(Math.max(((value - min) / (max - min)) * 100, 0), 100);

  // Gradient color based on percentage
  const getColor = (pct) => {
    if (pct < 40) return '#10B981'; // Green
    if (pct < 65) return '#F59E0B'; // Amber
    return '#EF4444'; // Rose
  };

  const currentColor = getColor(percentage);

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-white/[0.02] border border-white/5 rounded-2xl">
      <div className="relative w-48 h-24 overflow-hidden flex items-end justify-center">
        {/* Background Semi-circle */}
        <div className="absolute top-0 w-48 h-48 rounded-full border-[14px] border-white/10 border-b-transparent border-l-transparent -rotate-45" />

        {/* Dynamic Indicator fill */}
        <div
          className="absolute top-0 w-48 h-48 rounded-full border-[14px] border-b-transparent border-l-transparent transition-all duration-1000 ease-out"
          style={{
            borderColor: currentColor,
            transform: `rotate(${-45 + (percentage * 1.8)}deg)`,
            clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)',
          }}
        />

        {/* Center reading */}
        <div className="text-center z-10 -mb-2">
          <div className="text-4xl font-extrabold text-white tracking-tight">
            {value.toFixed(1)}
          </div>
          <div className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
            / {max}
          </div>
        </div>
      </div>

      <div className="mt-4 text-center">
        <h4 className="text-sm font-semibold text-slate-200">{label}</h4>
        <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>
        <div className="flex justify-between w-48 text-[10px] text-slate-400 mt-2 font-mono">
          <span>Min: {min}</span>
          <span className="text-amber-400">Median: 15.0</span>
          <span>Max: {max}</span>
        </div>
      </div>
    </div>
  );
}
