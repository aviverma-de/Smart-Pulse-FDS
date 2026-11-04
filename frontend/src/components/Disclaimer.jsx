import React from 'react';
import { AlertTriangle, Info } from 'lucide-react';

export default function Disclaimer({ variant = 'warning', className = '' }) {
  const isCaution = variant === 'caution';

  return (
    <div
      role="note"
      className={`rounded-2xl p-4 sm:p-5 border transition-all ${
        isCaution
          ? 'bg-amber-500/10 border-amber-500/30 text-amber-200'
          : 'bg-teal-500/10 border-teal-500/25 text-slate-300'
      } ${className}`}
    >
      <div className="flex items-start gap-3.5">
        <div className={`p-2 rounded-xl mt-0.5 shrink-0 ${
          isCaution ? 'bg-amber-500/20 text-amber-300' : 'bg-teal-500/20 text-teal-300'
        }`}>
          {isCaution ? <AlertTriangle className="w-4 h-4" /> : <Info className="w-4 h-4" />}
        </div>
        <div className="text-xs leading-relaxed space-y-1">
          <p className="font-semibold text-white tracking-wide uppercase text-[11px]">
            {isCaution ? 'Statistical & Simulation Notice' : 'Academic & Medical Disclaimer'}
          </p>
          <p className="text-slate-300">
            This tool provides <b>statistical estimates</b> derived from a university student research survey model (N = 132), 
            <b>not a clinical, psychiatric, or psychological diagnosis</b>. Observed relationships reflect statistical associations, not definitive causation.
          </p>
          <p className="text-slate-400">
            Recommendations are non-clinical, supportive wellness suggestions. If you are experiencing distress, academic pressure, or exhaustion, please connect with a licensed mental health professional or campus counseling services.
          </p>
        </div>
      </div>
    </div>
  );
}
