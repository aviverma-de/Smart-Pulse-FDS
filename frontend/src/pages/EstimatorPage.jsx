import React, { useState, useEffect, useRef } from 'react';
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Line, ComposedChart } from 'recharts';
import { SlidersHorizontal, ArrowRight, TrendingDown, TrendingUp, AlertTriangle, Sparkles, Scale, RefreshCw } from 'lucide-react';
import PageTransition from '../components/PageTransition';
import Card from '../components/Card';
import Gauge from '../components/Gauge';
import Disclaimer from '../components/Disclaimer';
import {
  PHONE_BED_OPTIONS,
  SLEEP_OPTIONS,
  WORKLOAD_OPTIONS,
  EXERCISE_OPTIONS,
  DEFAULT_ASSESSMENT
} from '../utils/constants';
import { simulateWhatIf, fetchPerformance, predictScore } from '../utils/api';

export default function EstimatorPage() {
  const [assessment, setAssessment] = useState(DEFAULT_ASSESSMENT);
  const [scoreData, setScoreData] = useState(null);
  const [perfData, setPerfData] = useState(null);
  const [whatIfInputs, setWhatIfInputs] = useState(DEFAULT_ASSESSMENT);
  const [whatIfResult, setWhatIfResult] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const debounceTimer = useRef(null);

  // Load existing assessment from session storage
  useEffect(() => {
    const cached = sessionStorage.getItem('smartpulse_assessment');
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        if (parsed.inputs) {
          setAssessment(parsed.inputs);
          setWhatIfInputs(parsed.inputs);
        }
        if (parsed.score) {
          setScoreData(parsed.score);
        }
      } catch (e) {
        console.error(e);
      }
    } else {
      // Calculate score for default inputs
      predictScore(DEFAULT_ASSESSMENT).then(setScoreData);
    }

    // Fetch actual-vs-predicted points
    fetchPerformance()
      .then((data) => setPerfData(data.regression))
      .catch((err) => console.error(err));
  }, []);

  // Run What-If simulation on modified inputs with 250ms debounce
  const triggerWhatIf = (newInputs) => {
    setWhatIfInputs(newInputs);
    setSimulating(true);

    if (debounceTimer.current) clearTimeout(debounceTimer.current);

    debounceTimer.current = setTimeout(async () => {
      try {
        const res = await simulateWhatIf(assessment, newInputs);
        setWhatIfResult(res);
      } catch (err) {
        console.error('What-if failed', err);
      } finally {
        setSimulating(false);
      }
    }, 250);
  };

  const handleWhatIfChange = (field, val) => {
    const updated = { ...whatIfInputs, [field]: val };
    triggerWhatIf(updated);
  };

  const currentScore = scoreData?.predicted_score ?? 15.0;
  const simulatedScore = whatIfResult?.modified?.score ?? currentScore;
  const scoreDiff = whatIfResult?.score_difference ?? 0.0;
  const hasImproved = scoreDiff < -0.1;
  const hasWorsened = scoreDiff > 0.1;

  // Prepare Scatter data: actual vs predicted from real N=132 regression model
  const scatterPoints = perfData?.actual_vs_predicted || [];
  const userPoint = [
    { actual: currentScore, predicted: currentScore, id: 'You', isUser: true },
  ];

  return (
    <PageTransition className="max-w-6xl mx-auto px-4 py-8 space-y-10">
      {/* Page Title */}
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold text-teal-400 uppercase tracking-wider mb-1">
          <span>Continuous Scale Modeling & Counterfactual Simulator</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Burnout Score Estimator & What-If Simulator
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Continuous target: <code className="text-teal-300">burnout_total</code> (5 to 25 scale). Evaluated via Bayesian linear regression posterior means and OLS.
        </p>
      </div>

      {/* SECTION 1: SCORE ESTIMATOR GAUGE & SCALE CONTEXT */}
      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1 flex flex-col justify-between" glow>
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4">
              Estimated Score
            </h3>
            <Gauge
              value={currentScore}
              min={scoreData?.scale_min ?? 5}
              max={scoreData?.scale_max ?? 25}
              label="Burnout Total"
              subtitle="5 to 25 Scale"
            />
          </div>

          <div className="mt-6 pt-4 border-t border-white/10 space-y-2 text-xs text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-400">94% Credible Interval:</span>
              <span className="font-mono text-teal-300">
                [{scoreData?.credible_interval_94?.[0]?.toFixed(1) ?? '10.2'}, {scoreData?.credible_interval_94?.[1]?.toFixed(1) ?? '18.8'}]
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Cohort Percentile:</span>
              <span className="font-mono text-cyan-300">
                {scoreData?.percentile?.toFixed(1) ?? '50.0'}th percentile
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Sample Baseline Median:</span>
              <span className="font-mono text-amber-300">15.0</span>
            </div>
          </div>
        </Card>

        {/* SECTION 2: ACTUAL VS PREDICTED SCATTER PLOT */}
        <Card
          className="lg:col-span-2"
          title="Actual vs. Predicted Model Fit (N = 132)"
          subtitle="Observed test set points along with the ideal y = x reference line. Your estimate is marked."
        >
          <div className="h-64 sm:h-72 w-full mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                <XAxis
                  type="number"
                  dataKey="predicted"
                  name="Predicted Burnout"
                  domain={[5, 25]}
                  stroke="#94A3B8"
                  fontSize={11}
                  unit=" pts"
                />
                <YAxis
                  type="number"
                  dataKey="actual"
                  name="Actual Burnout"
                  domain={[5, 25]}
                  stroke="#94A3B8"
                  fontSize={11}
                  unit=" pts"
                />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{
                    backgroundColor: '#0F172A',
                    borderColor: '#334155',
                    borderRadius: '12px',
                    color: '#F8FAFC',
                    fontSize: '12px',
                  }}
                  formatter={(val, name) => [`${val} pts`, name]}
                />
                {/* Cohort student points */}
                <Scatter
                  name="Cohort Students (N=132)"
                  data={scatterPoints}
                  fill="#0D9488"
                  opacity={0.65}
                />
                {/* User point marked on chart */}
                <Scatter
                  name="Your Prediction"
                  data={userPoint}
                  fill="#F43F5E"
                  shape="star"
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-teal-500 inline-block" />
                <span>Survey Respondents (N = 132)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
                <span className="text-white font-medium">Your Assessment</span>
              </div>
            </div>
            <span className="font-mono text-teal-400 text-[11px]">
              R² = {perfData?.r2 ?? '0.19'}, MAE = {perfData?.mae ?? '2.94'} pts
            </span>
          </div>
        </Card>
      </div>

      {/* SECTION 3: WHAT-IF SIMULATOR */}
      <Card
        title="Interactive What-If Habit Simulator"
        subtitle="Adjust your daily routines below to observe how the statistical model shifts its burnout estimate."
      >
        <div className="grid md:grid-cols-2 gap-8 mt-2">
          {/* Left: Interactive Controls (Only real model features) */}
          <div className="space-y-4">
            <h4 className="text-xs font-bold text-teal-400 uppercase tracking-wider mb-2">
              Adjustable Lifestyle Predictors (Real Model Features)
            </h4>

            {/* Control 1: Bedtime Phone Usage */}
            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-2">
              <div className="flex justify-between text-xs">
                <label className="font-semibold text-slate-200">Bedtime Smartphone Usage</label>
                <span className="text-teal-300 font-mono">
                  {PHONE_BED_OPTIONS.find((p) => p.value === whatIfInputs.phone_bed_code)?.label}
                </span>
              </div>
              <select
                value={whatIfInputs.phone_bed_code}
                onChange={(e) => handleWhatIfChange('phone_bed_code', parseInt(e.target.value, 10))}
                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-xs focus:outline-none focus:border-teal-400"
              >
                {PHONE_BED_OPTIONS.map((p) => (
                  <option key={p.value} value={p.value} className="bg-[#0F172A]">
                    {p.label} — {p.desc}
                  </option>
                ))}
              </select>
            </div>

            {/* Control 2: Sleep Duration */}
            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-2">
              <div className="flex justify-between text-xs">
                <label className="font-semibold text-slate-200">Nightly Sleep Duration</label>
                <span className="text-teal-300 font-mono">{whatIfInputs.sleep_mid_hrs} hrs</span>
              </div>
              <select
                value={whatIfInputs.sleep_mid_hrs}
                onChange={(e) => handleWhatIfChange('sleep_mid_hrs', parseFloat(e.target.value))}
                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-xs focus:outline-none focus:border-teal-400"
              >
                {SLEEP_OPTIONS.map((s) => (
                  <option key={s.value} value={s.value} className="bg-[#0F172A]">
                    {s.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Control 3: Perceived Workload */}
            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-2">
              <div className="flex justify-between text-xs">
                <label className="font-semibold text-slate-200">Perceived Study Workload</label>
                <span className="text-teal-300 font-mono">
                  {WORKLOAD_OPTIONS.find((w) => w.value === whatIfInputs.workload_code)?.label}
                </span>
              </div>
              <select
                value={whatIfInputs.workload_code}
                onChange={(e) => handleWhatIfChange('workload_code', parseInt(e.target.value, 10))}
                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-xs focus:outline-none focus:border-teal-400"
              >
                {WORKLOAD_OPTIONS.map((w) => (
                  <option key={w.value} value={w.value} className="bg-[#0F172A]">
                    {w.label} — {w.desc}
                  </option>
                ))}
              </select>
            </div>

            {/* Control 4: Exercise Frequency */}
            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-2">
              <div className="flex justify-between text-xs">
                <label className="font-semibold text-slate-200">Exercise Days / Week</label>
                <span className="text-teal-300 font-mono">{whatIfInputs.exercise_days_mid} days</span>
              </div>
              <select
                value={whatIfInputs.exercise_days_mid}
                onChange={(e) => handleWhatIfChange('exercise_days_mid', parseFloat(e.target.value))}
                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-xs focus:outline-none focus:border-teal-400"
              >
                {EXERCISE_OPTIONS.map((ex) => (
                  <option key={ex.value} value={ex.value} className="bg-[#0F172A]">
                    {ex.label}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="button"
              onClick={() => triggerWhatIf(assessment)}
              className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors pt-2"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset simulator to original assessment</span>
            </button>
          </div>

          {/* Right: Side-by-Side Comparison Output */}
          <div className="flex flex-col justify-between bg-white/[0.02] border border-white/10 rounded-2xl p-6">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-white/10">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Scenario Comparison
                </h4>
                {simulating && (
                  <span className="text-[11px] text-teal-400 animate-pulse font-mono">
                    Computing live prediction...
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 my-6 text-center">
                {/* Original Score */}
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="text-[11px] text-slate-400 uppercase font-semibold">
                    Current Score
                  </div>
                  <div className="text-3xl font-extrabold text-white mt-1">
                    {currentScore.toFixed(1)}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {scoreData?.percentile?.toFixed(0) || '50'}th percentile
                  </div>
                </div>

                {/* Simulated Score */}
                <div className="p-4 rounded-xl bg-teal-500/10 border border-teal-500/20">
                  <div className="text-[11px] text-teal-300 uppercase font-semibold">
                    Simulated Score
                  </div>
                  <div className="text-3xl font-extrabold text-teal-200 mt-1">
                    {simulatedScore.toFixed(1)}
                  </div>
                  <div className="text-xs text-teal-400 mt-1">
                    Hypothetical projection
                  </div>
                </div>
              </div>

              {/* Delta Box */}
              <div className={`p-4 rounded-xl border flex items-center justify-between ${
                hasImproved
                  ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300'
                  : hasWorsened
                  ? 'bg-rose-500/15 border-rose-500/30 text-rose-300'
                  : 'bg-white/5 border-white/10 text-slate-300'
              }`}>
                <div className="flex items-center gap-2.5">
                  {hasImproved ? (
                    <TrendingDown className="w-5 h-5 text-emerald-400" />
                  ) : hasWorsened ? (
                    <TrendingUp className="w-5 h-5 text-rose-400" />
                  ) : (
                    <Scale className="w-5 h-5 text-slate-400" />
                  )}
                  <div>
                    <div className="text-xs font-bold">
                      {hasImproved ? 'Estimated Improvement' : hasWorsened ? 'Estimated Elevated Strain' : 'Minimal Delta'}
                    </div>
                    <div className="text-[11px] opacity-80">
                      {hasImproved
                        ? 'Simulated change shifts continuous score downward.'
                        : hasWorsened
                        ? 'Simulated change increases estimated burnout total.'
                        : 'Parameters yield equivalent projection.'}
                    </div>
                  </div>
                </div>
                <div className="text-xl font-mono font-extrabold">
                  {scoreDiff > 0 ? `+${scoreDiff.toFixed(1)}` : scoreDiff.toFixed(1)} pts
                </div>
              </div>

              {whatIfResult?.category_changed && (
                <div className="mt-3 p-2.5 rounded-lg bg-teal-500/20 border border-teal-500/40 text-teal-200 text-xs text-center font-bold">
                  Class Transition Triggered: {whatIfResult.baseline.category} ➔ {whatIfResult.modified.category}
                </div>
              )}
            </div>

            {/* Caution statement */}
            <div className="mt-6 pt-4 border-t border-white/10 flex items-start gap-2.5 text-[11px] text-slate-400 leading-relaxed">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <span>
                <b>Caution:</b> These are hypothetical model scenarios illustrating model sensitivity. Because this is a cross-sectional study (N = 132), these results demonstrate statistical associations, not definitive proof that changing an isolated habit will mechanically reduce burnout.
              </span>
            </div>
          </div>
        </div>
      </Card>

      <Disclaimer />
    </PageTransition>
  );
}
