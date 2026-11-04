import React from 'react';
import { ShieldCheck, Heart } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-white/10 bg-[#0B1220]/90 text-slate-400 py-10 px-4 sm:px-6 lg:px-8 mt-20">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 text-white font-bold text-lg">
            <span>SmartPulse</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20 font-normal">
              FDS Final Project
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-md">
            "Understand stress. Predict burnout. Take action." A university research platform analyzing lifestyle correlates of academic burnout (N = 132).
          </p>
        </div>

        <div className="flex items-center gap-6 text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-teal-400" />
            <span>Strict Privacy: No Login Required</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Heart className="w-4 h-4 text-rose-400" />
            <span>Supportive Non-Clinical Tool</span>
          </div>
        </div>
      </div>
      <div className="max-w-7xl mx-auto mt-6 pt-6 border-t border-white/5 text-center text-[11px] text-slate-500">
        Foundations of Data Science Coursework • Statistical Learning & Bayesian Linear Regression • Educational & Research Purposes Only.
      </div>
    </footer>
  );
}
