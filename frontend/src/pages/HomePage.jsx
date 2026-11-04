import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, BrainCircuit, SlidersHorizontal, Users, Flame, Activity, Moon, Sparkles } from 'lucide-react';
import PageTransition from '../components/PageTransition';
import StatCard from '../components/StatCard';
import { fetchOverview } from '../utils/api';
import Disclaimer from '../components/Disclaimer';

export default function HomePage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOverview()
      .then((data) => setStats(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <PageTransition className="space-y-16 py-8">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-8 pb-12 sm:pt-14 sm:pb-16 text-center max-w-4xl mx-auto px-4">
        {/* Glow ambient circle */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-gradient-to-tr from-teal-500/15 via-cyan-500/10 to-transparent blur-3xl -z-10 rounded-full" />

        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/25 text-teal-300 text-xs font-semibold mb-6 shadow-sm">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Tagline: "Understand stress. Predict burnout. Take action."</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-[1.15]">
          Understand your well-being.{' '}
          <span className="bg-gradient-to-r from-teal-400 via-cyan-300 to-teal-200 bg-clip-text text-transparent">
            Take control of your academic balance.
          </span>
        </h1>

        <p className="mt-6 text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
          SmartPulse translates student lifestyle patterns into personalized risk forecasts and supportive wellness recommendations. Powered by validated machine learning and Bayesian regression (N = 132).
        </p>

        {/* CTA Buttons */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/assessment"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold text-sm shadow-lg shadow-teal-500/25 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <span>Start Assessment</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/dashboard"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-white/5 hover:bg-white/10 text-white font-semibold text-sm border border-white/10 transition-all hover:border-white/20"
          >
            Explore Dashboard
          </Link>
        </div>
      </section>

      {/* SmartPulse at a Glance Strip */}
      <section className="max-w-6xl mx-auto px-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xs font-bold text-teal-400 tracking-wider uppercase">
            SmartPulse at a glance • Real University Cohort Data
          </h2>
          <span className="text-xs text-slate-400 font-mono">100% Empirically Computed</span>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Students Surveyed"
            value={stats?.n_students ?? 132}
            suffix="Cohort"
            subtitle="Undergraduate & PG students"
            icon={Users}
            color="teal"
          />
          <StatCard
            title="Avg Burnout Score"
            value={stats?.mean_burnout ?? 14.98}
            decimals={2}
            suffix="/ 25"
            subtitle="Median cutoff = 15.0"
            icon={Flame}
            color="rose"
          />
          <StatCard
            title="Avg Stress Level"
            value={stats?.mean_stress ?? 11.66}
            decimals={2}
            suffix="/ 20"
            subtitle="PSS-4 self-reported total"
            icon={Activity}
            color="amber"
          />
          <StatCard
            title="Avg Sleep Duration"
            value={stats?.mean_sleep ?? 6.55}
            decimals={2}
            suffix="hrs"
            subtitle="Typical nightly rest"
            icon={Moon}
            color="cyan"
          />
        </div>
      </section>

      {/* Two Explore Cards */}
      <section className="max-w-6xl mx-auto px-4">
        <div className="grid md:grid-cols-2 gap-6">
          {/* Card 1: AI Predictions */}
          <div className="glass-panel glass-panel-hover rounded-2xl p-8 border border-white/10 relative overflow-hidden group">
            <div className="w-12 h-12 rounded-2xl bg-teal-500/15 border border-teal-500/30 text-teal-400 flex items-center justify-center mb-6 shadow-md shadow-teal-500/10">
              <BrainCircuit className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">
              AI Burnout Prediction & Transparent Attributions
            </h3>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-6">
              Complete the validated 9-item lifestyle questionnaire. Receive an immediate risk categorization from our 500-tree Random Forest classifier and understand top driving factors through transparent log-odds attributions.
            </p>
            <Link
              to="/assessment"
              className="inline-flex items-center gap-2 text-teal-300 text-xs sm:text-sm font-semibold hover:text-teal-200 transition-colors"
            >
              <span>Launch Well-being Assessment</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>

          {/* Card 2: Score Estimator & What-If Simulator */}
          <div className="glass-panel glass-panel-hover rounded-2xl p-8 border border-white/10 relative overflow-hidden group">
            <div className="w-12 h-12 rounded-2xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 flex items-center justify-center mb-6 shadow-md shadow-cyan-500/10">
              <SlidersHorizontal className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">
              Continuous Score Estimator & What-If Simulator
            </h3>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-6">
              Estimate your continuous burnout total on a 5 to 25 scale with 94% credible intervals. Interactively adjust routine habits (bedtime phone use, sleep duration, study workload) in real-time to observe hypothetical projections.
            </p>
            <Link
              to="/estimator"
              className="inline-flex items-center gap-2 text-cyan-300 text-xs sm:text-sm font-semibold hover:text-cyan-200 transition-colors"
            >
              <span>Explore Score & What-If Simulator</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </section>

      {/* Mandatory Disclaimer */}
      <section className="max-w-6xl mx-auto px-4">
        <Disclaimer />
      </section>
    </PageTransition>
  );
}
