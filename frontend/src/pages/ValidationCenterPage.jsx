import React, { useState, useEffect } from 'react';
import {
  ShieldCheck, AlertTriangle, RefreshCw, Database, Award, ArrowUpRight,
  TrendingUp, CheckCircle2, XCircle, Info, Sparkles, SlidersHorizontal, Lock
} from 'lucide-react';
import {
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, Tooltip,
  CartesianGrid, ReferenceLine, BarChart, Bar, Cell
} from 'recharts';
import PageTransition from '../components/PageTransition';
import Card from '../components/Card';
import StatCard from '../components/StatCard';
import Disclaimer from '../components/Disclaimer';
import {
  fetchValidationSummary,
  fetchValidationClassification,
  fetchValidationRegression,
  fetchValidationFeedback,
  fetchValidationErrors,
  fetchValidationModels,
  adminRetrain,
  adminRollback,
  adminSeedDemo
} from '../utils/api';

export default function ValidationCenterPage() {
  const [adminToken, setAdminToken] = useState(
    () => localStorage.getItem('smartpulse_admin_token') || ''
  );
  const [tokenInput, setTokenInput] = useState('');
  const [authError, setAuthError] = useState(false);
  const [includeDemo, setIncludeDemo] = useState(false);

  const [loading, setLoading] = useState(true);
  const [retrainingLoading, setRetrainingLoading] = useState(false);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);

  const [summary, setSummary] = useState(null);
  const [classification, setClassification] = useState(null);
  const [regression, setRegression] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [errorsData, setErrorsData] = useState(null);
  const [modelsData, setModelsData] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, clsRes, regRes, fbRes, errRes, modRes] = await Promise.all([
        fetchValidationSummary(includeDemo, adminToken),
        fetchValidationClassification(includeDemo, adminToken),
        fetchValidationRegression(includeDemo, adminToken),
        fetchValidationFeedback(includeDemo, adminToken),
        fetchValidationErrors(includeDemo, adminToken),
        fetchValidationModels(adminToken),
      ]);
      setSummary(sumRes);
      setClassification(clsRes);
      setRegression(regRes);
      setFeedback(fbRes);
      setErrorsData(errRes);
      setModelsData(modRes);
      setAuthError(false);
    } catch (err) {
      if (err.message === 'ADMIN_AUTH_REQUIRED') {
        setAuthError(true);
      } else {
        setError(err.message || 'Failed to load validation metrics.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [includeDemo, adminToken]);

  const handleSaveToken = (e) => {
    e.preventDefault();
    if (tokenInput.trim()) {
      localStorage.setItem('smartpulse_admin_token', tokenInput.trim());
      setAdminToken(tokenInput.trim());
      setAuthError(false);
    }
  };

  const handleRetrain = async (force = false) => {
    setRetrainingLoading(true);
    setNotification(null);
    try {
      const res = await adminRetrain(includeDemo, force, adminToken);
      if (res.status === 'promoted') {
        setNotification({
          type: 'success',
          title: `Candidate Promoted to ${res.version}!`,
          msg: `New model achieved Macro-F1 ${res.candidate_evaluation?.macro_f1} (Gain: ${res.f1_gain >= 0 ? '+' : ''}${res.f1_gain}). High-burnout recall: ${res.candidate_evaluation?.high_recall}.`
        });
      } else if (res.status === 'rejected') {
        setNotification({
          type: 'warning',
          title: 'Candidate Model Rejected',
          msg: `Candidate failed promotion criteria: ${res.rejection_reasons?.join(' ') || 'Did not outperform active model.'}`
        });
      } else if (res.status === 'refused') {
        setNotification({
          type: 'info',
          title: 'Insufficient Verified Outcomes',
          msg: `${res.message} Need ${res.needed_count} more verified outcomes before retraining.`
        });
      }
      loadData();
    } catch (err) {
      setNotification({ type: 'error', title: 'Retraining Error', msg: err.message });
    } finally {
      setRetrainingLoading(false);
    }
  };

  const handleRollback = async (targetVer) => {
    setRetrainingLoading(true);
    setNotification(null);
    try {
      const res = await adminRollback(targetVer, adminToken);
      setNotification({ type: 'success', title: 'Rollback Complete', msg: res.message });
      loadData();
    } catch (err) {
      setNotification({ type: 'error', title: 'Rollback Error', msg: err.message });
    } finally {
      setRetrainingLoading(false);
    }
  };

  const handleSeedDemo = async () => {
    setLoading(true);
    try {
      await adminSeedDemo(35, adminToken);
      setIncludeDemo(true);
      setNotification({
        type: 'info',
        title: 'Demo Data Seeded',
        msg: 'Seeded 35 demo validation outcomes (is_demo=true). Real metrics remain untouched when demo toggle is off.'
      });
      loadData();
    } catch (err) {
      setNotification({ type: 'error', title: 'Seeding Error', msg: err.message });
      setLoading(false);
    }
  };

  if (authError) {
    return (
      <PageTransition className="max-w-md mx-auto px-4 py-20 text-center space-y-6">
        <div className="w-14 h-14 rounded-2xl bg-amber-500/15 border border-amber-500/30 text-amber-400 flex items-center justify-center mx-auto">
          <Lock className="w-7 h-7" />
        </div>
        <h2 className="text-2xl font-bold text-white">Admin Authentication Required</h2>
        <p className="text-xs text-slate-300">
          The Validation Center and Retraining Pipeline are restricted by the <code>ADMIN_TOKEN</code> environment variable.
        </p>
        <form onSubmit={handleSaveToken} className="space-y-3">
          <input
            type="password"
            placeholder="Enter ADMIN_TOKEN"
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/15 text-white text-sm focus:outline-none focus:border-teal-500"
            required
          />
          <button
            type="submit"
            className="w-full py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all"
          >
            Authenticate & Access Center
          </button>
        </form>
      </PageTransition>
    );
  }

  const n = summary?.n || 0;
  const isLowSample = summary?.is_low_sample ?? true;
  const progressPct = summary?.progress_pct || 0;

  return (
    <PageTransition className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-teal-400 uppercase tracking-wider mb-1">
            <ShieldCheck className="w-4 h-4 text-teal-400" />
            <span>Audited Performance & Controlled Retraining</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Validation Center
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Active Model: <span className="font-bold text-teal-300">{summary?.active_version || 'v1.0'}</span> • Evaluated against independent verified actuals only.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Demo toggle */}
          <label className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-300 cursor-pointer hover:bg-white/10 transition-all select-none">
            <input
              type="checkbox"
              checked={includeDemo}
              onChange={(e) => setIncludeDemo(e.target.checked)}
              className="rounded accent-teal-500 w-3.5 h-3.5"
            />
            <span>Include Demo Data</span>
          </label>

          <button
            onClick={() => handleRetrain(false)}
            disabled={retrainingLoading}
            className="px-4 py-2 rounded-xl bg-teal-500 hover:bg-teal-400 disabled:opacity-50 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${retrainingLoading ? 'animate-spin' : ''}`} />
            <span>Retrain Candidate</span>
          </button>

          <button
            onClick={handleSeedDemo}
            className="px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-xs font-semibold transition-all"
            title="Seed demo validation records to test UI charts"
          >
            + Seed Demo (35)
          </button>
        </div>
      </div>

      {/* DEMO DATA Banner */}
      {includeDemo && (
        <div className="p-3.5 rounded-xl bg-amber-500/20 border-2 border-amber-500/40 text-amber-200 text-xs flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded font-black bg-amber-500 text-slate-950 text-[10px] tracking-wider uppercase">
              DEMO DATA INCLUDED
            </span>
            <span>You are viewing metrics that include flagged demo rows. Real statistical audits exclude demo data.</span>
          </div>
          <button
            onClick={() => setIncludeDemo(false)}
            className="underline font-bold text-amber-300 hover:text-white"
          >
            Turn Off Demo Data
          </button>
        </div>
      )}

      {/* Notification Toast */}
      {notification && (
        <div className={`p-4 rounded-xl border text-xs flex items-start justify-between gap-3 ${
          notification.type === 'success'
            ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300'
            : notification.type === 'warning'
            ? 'bg-amber-500/15 border-amber-500/30 text-amber-300'
            : notification.type === 'info'
            ? 'bg-teal-500/15 border-teal-500/30 text-teal-300'
            : 'bg-rose-500/15 border-rose-500/30 text-rose-300'
        }`}>
          <div>
            <strong className="block text-sm font-bold text-white mb-0.5">{notification.title}</strong>
            <p className="leading-relaxed">{notification.msg}</p>
          </div>
          <button onClick={() => setNotification(null)} className="text-slate-400 hover:text-white text-sm font-bold">
            ✕
          </button>
        </div>
      )}

      {/* 1. KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Validated N */}
        <Card className="p-5">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Verified Actuals (n)
          </span>
          <div className="text-3xl font-black text-white">
            {n}
            <small className="text-xs text-slate-400 font-normal ml-1">samples</small>
          </div>
          <span className="text-[11px] text-slate-400 mt-2 block">
            Target: 30 verified outcomes
          </span>
        </Card>

        {/* Classification Accuracy */}
        <Card className="p-5">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Measured Accuracy (n={n})
          </span>
          <div className="text-3xl font-black text-teal-400">
            {n === 0
              ? 'Not yet established (n=0)'
              : `${(summary?.classification?.accuracy * 100).toFixed(1)}%`}
          </div>
          <span className="text-[11px] text-slate-400 mt-2 block">
            {summary?.classification?.accuracy_ci
              ? `Wilson 95% CI: [${(summary.classification.accuracy_ci[0] * 100).toFixed(1)}%, ${(summary.classification.accuracy_ci[1] * 100).toFixed(1)}%]`
              : 'CI requires n ≥ 1'}
          </span>
        </Card>

        {/* Regression MAE */}
        <Card className="p-5">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Mean Absolute Error (n={n})
          </span>
          <div className="text-3xl font-black text-cyan-400">
            {n === 0
              ? 'Not yet established (n=0)'
              : `${summary?.regression?.mae?.toFixed(2)} pts`}
          </div>
          <span className="text-[11px] text-slate-400 mt-2 block">
            {summary?.regression?.mae_ci
              ? `Bootstrap 95% CI: [${summary.regression.mae_ci[0]}, ${summary.regression.mae_ci[1]}]`
              : '5–25 burnout total scale'}
          </span>
        </Card>

        {/* Subjective Agreement */}
        <Card className="p-5">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Student Agreement
            </span>
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/10 text-slate-300 font-bold uppercase">
              Subjective
            </span>
          </div>
          <div className="text-3xl font-black text-purple-400">
            {summary?.feedback?.n === 0
              ? 'Not yet established'
              : `${summary?.feedback?.agreement_pct?.toFixed(1) || 0}%`}
          </div>
          <span className="text-[11px] text-slate-400 mt-2 block">
            Labelled "not ground truth" (n={summary?.feedback?.n || 0})
          </span>
        </Card>
      </div>

      {/* 2. Data Collection Progress & Low Sample Guard */}
      <Card
        title={`Data Collection Progress (${n} / 30 required outcomes)`}
        subtitle={isLowSample ? 'Low Sample Safeguard Active (< 30 verified outcomes)' : 'Minimum sample threshold achieved.'}
      >
        <div className="space-y-3">
          <div className="flex justify-between text-xs text-slate-300 font-semibold">
            <span>Progress toward verified statistical maturity:</span>
            <span>{progressPct}% ({n}/30)</span>
          </div>
          <div className="h-3 w-full bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                isLowSample ? 'bg-amber-400' : 'bg-teal-400'
              }`}
              style={{ width: `${progressPct}%` }}
            />
          </div>
          {isLowSample && (
            <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>
                Low-sample warning: n is below the required 30 minimum. Confusion matrices and R² estimates reflect preliminary trends only.
              </span>
            </div>
          )}
        </div>
      </Card>

      {/* 3. Classification Metrics & Confusion Matrix */}
      <div className="grid lg:grid-cols-2 gap-6">
        <Card
          title={`Classification Performance vs MEASURED Actuals (n=${classification?.n || 0})`}
          subtitle="Strictly audited against independent verified ground-truth categories."
        >
          {classification?.n === 0 ? (
            <div className="py-12 text-center text-xs text-slate-400">
              Not yet established (n=0). Awaiting verified student outcomes.
            </div>
          ) : (
            <div className="space-y-4">
              {/* High Burnout Recall Callout */}
              <div className="p-4 rounded-xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-teal-300 uppercase tracking-wider block">
                    High-Burnout Recall (Primary Screening Goal)
                  </span>
                  <p className="text-xs text-slate-300 mt-0.5">
                    Fraction of truly high-burnout students correctly identified:
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-black text-teal-400">
                    {((classification?.high_burnout_recall || 0) * 100).toFixed(1)}%
                  </span>
                  {classification?.high_burnout_recall_ci && (
                    <span className="block text-[10px] text-slate-400">
                      CI: [{(classification.high_burnout_recall_ci[0] * 100).toFixed(1)}%, {(classification.high_burnout_recall_ci[1] * 100).toFixed(1)}%]
                    </span>
                  )}
                </div>
              </div>

              {/* Metrics Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-white/10 text-slate-400">
                    <tr>
                      <th className="pb-2">Metric</th>
                      <th className="pb-2 text-right">Value (n={classification?.n})</th>
                      <th className="pb-2 text-right">95% Confidence Interval</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-slate-200">
                    <tr>
                      <td className="py-2.5 font-semibold">Overall Accuracy</td>
                      <td className="py-2.5 text-right font-bold text-white">
                        {((classification?.accuracy || 0) * 100).toFixed(1)}%
                      </td>
                      <td className="py-2.5 text-right text-slate-400">
                        {classification?.accuracy_ci
                          ? `[${(classification.accuracy_ci[0] * 100).toFixed(1)}%, ${(classification.accuracy_ci[1] * 100).toFixed(1)}%]`
                          : '—'}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2.5 font-semibold">Macro-Averaged F1</td>
                      <td className="py-2.5 text-right font-bold text-white">
                        {classification?.macro_f1?.toFixed(3)}
                      </td>
                      <td className="py-2.5 text-right text-slate-400">Balanced across classes</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 font-semibold">Weighted F1</td>
                      <td className="py-2.5 text-right font-bold text-white">
                        {classification?.weighted_f1?.toFixed(3)}
                      </td>
                      <td className="py-2.5 text-right text-slate-400">Sample-weighted</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 font-semibold">Macro Precision</td>
                      <td className="py-2.5 text-right font-bold text-white">
                        {((classification?.macro_precision || 0) * 100).toFixed(1)}%
                      </td>
                      <td className="py-2.5 text-right text-slate-400">Mean precision</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Card>

        {/* Confusion Matrix Heatmap */}
        <Card
          title={`Confusion Matrix Heatmap (vs Measured Only, n=${classification?.n || 0})`}
          subtitle="Rows = Measured Ground Truth, Columns = Predicted Category"
        >
          {classification?.n === 0 ? (
            <div className="py-12 text-center text-xs text-slate-400">
              Not yet established (n=0)
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div />
                <div className="p-2 font-bold text-teal-400 bg-white/5 rounded-lg">Pred: High</div>
                <div className="p-2 font-bold text-emerald-400 bg-white/5 rounded-lg">Pred: Low</div>

                {/* Row 1: Actual High */}
                <div className="p-2 font-bold text-teal-400 bg-white/5 rounded-lg flex items-center justify-center">
                  True: High
                </div>
                <div className="p-5 rounded-xl bg-teal-500/20 border border-teal-500/40 font-black text-2xl text-teal-300">
                  {classification?.confusion_matrix?.[0]?.[0] ?? 0}
                  <span className="block text-[10px] font-semibold text-slate-400 mt-1">True Positive (TP)</span>
                </div>
                <div className="p-5 rounded-xl bg-rose-500/20 border border-rose-500/40 font-black text-2xl text-rose-300">
                  {classification?.confusion_matrix?.[0]?.[1] ?? 0}
                  <span className="block text-[10px] font-semibold text-slate-400 mt-1">False Negative (FN)</span>
                </div>

                {/* Row 2: Actual Low */}
                <div className="p-2 font-bold text-emerald-400 bg-white/5 rounded-lg flex items-center justify-center">
                  True: Low
                </div>
                <div className="p-5 rounded-xl bg-amber-500/20 border border-amber-500/40 font-black text-2xl text-amber-300">
                  {classification?.confusion_matrix?.[1]?.[0] ?? 0}
                  <span className="block text-[10px] font-semibold text-slate-400 mt-1">False Positive (FP)</span>
                </div>
                <div className="p-5 rounded-xl bg-emerald-500/20 border border-emerald-500/40 font-black text-2xl text-emerald-300">
                  {classification?.confusion_matrix?.[1]?.[1] ?? 0}
                  <span className="block text-[10px] font-semibold text-slate-400 mt-1">True Negative (TN)</span>
                </div>
              </div>

              <p className="text-[11px] text-slate-400 text-center leading-relaxed">
                Evaluated strictly against verified 5-item burnout battery actuals. Student feedback agreement is never used as actual ground truth.
              </p>
            </div>
          )}
        </Card>
      </div>

      {/* 4. Regression Analysis: Actual vs Predicted & Residuals */}
      <Card
        title={`Continuous Regression Evaluation (n=${regression?.n || 0})`}
        subtitle="Scatter plot of Actual Measured Score vs Predicted Score with ideal 45° line."
      >
        {regression?.n === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            Not yet established (n=0). Awaiting continuous verified scores.
          </div>
        ) : (
          <div className="space-y-6">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                  <XAxis
                    type="number"
                    dataKey="predicted"
                    name="Predicted Score"
                    domain={[5, 25]}
                    stroke="#94A3B8"
                    fontSize={11}
                    unit=" pts"
                  />
                  <YAxis
                    type="number"
                    dataKey="actual"
                    name="Actual Measured Score"
                    domain={[5, 25]}
                    stroke="#94A3B8"
                    fontSize={11}
                    unit=" pts"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0F172A',
                      borderColor: '#334155',
                      borderRadius: '12px',
                      color: '#F8FAFC',
                      fontSize: '12px',
                    }}
                    cursor={{ strokeDasharray: '3 3' }}
                  />
                  {/* Ideal diagonal y = x reference line */}
                  <ReferenceLine
                    segment={[{ x: 5, y: 5 }, { x: 25, y: 25 }]}
                    stroke="#14B8A6"
                    strokeDasharray="4 4"
                    strokeWidth={2}
                    label={{ value: 'Ideal y = x', fill: '#14B8A6', fontSize: 11, position: 'top' }}
                  />
                  <Scatter
                    name="Students"
                    data={regression?.pairs || []}
                    fill="#38BDF8"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>

            {/* Regression Summary Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-white/10 text-center">
              <div className="p-3 rounded-xl bg-white/[0.02]">
                <span className="text-[10px] uppercase font-bold text-slate-400">MAE (n={regression?.n})</span>
                <span className="block text-lg font-bold text-white mt-0.5">{regression?.mae} pts</span>
              </div>
              <div className="p-3 rounded-xl bg-white/[0.02]">
                <span className="text-[10px] uppercase font-bold text-slate-400">RMSE (n={regression?.n})</span>
                <span className="block text-lg font-bold text-white mt-0.5">{regression?.rmse} pts</span>
              </div>
              <div className="p-3 rounded-xl bg-white/[0.02]">
                <span className="text-[10px] uppercase font-bold text-slate-400">R² Coefficient</span>
                <span className="block text-lg font-bold text-white mt-0.5">{regression?.r2}</span>
              </div>
              <div className="p-3 rounded-xl bg-white/[0.02]">
                <span className="text-[10px] uppercase font-bold text-slate-400">Residual Mean ± SD</span>
                <span className="block text-lg font-bold text-white mt-0.5">{regression?.residual_mean} ± {regression?.residual_std}</span>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* 5. Subjective Student Feedback Analytics & Cross-Tab */}
      <Card
        title={`Subjective Student Feedback (Not Ground Truth, n=${feedback?.n || 0})`}
        subtitle="Stored separately from ground-truth outcomes. Analyzes user perception vs measured accuracy."
      >
        {feedback?.n === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            Not yet established (n=0). No subjective feedback submitted yet.
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-6">
            {/* Agreement Breakdown */}
            <div className="space-y-4">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                "How well does this describe your current condition?"
              </h4>
              <div className="space-y-2">
                {Object.entries(feedback?.percentages || {}).map(([key, val]) => (
                  <div key={key}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">{key}</span>
                      <span className="font-bold text-white">{val}% ({feedback.counts[key]})</span>
                    </div>
                    <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          key === 'Yes' ? 'bg-teal-400' : key === 'No' ? 'bg-rose-400' : 'bg-slate-400'
                        }`}
                        style={{ width: `${val}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Cross-Tabulation */}
            <div className="space-y-4">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Cross-Tabulation: Feedback vs Measured Correctness
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-white/10 text-slate-400">
                    <tr>
                      <th className="pb-2">Feedback</th>
                      <th className="pb-2 text-center text-emerald-400">Model Correct</th>
                      <th className="pb-2 text-center text-rose-400">Model Incorrect</th>
                      <th className="pb-2 text-center text-slate-400">Unverified</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-slate-200">
                    {Object.entries(feedback?.cross_tabulation || {}).map(([cat, counts]) => (
                      <tr key={cat}>
                        <td className="py-2 font-semibold text-white">{cat}</td>
                        <td className="py-2 text-center font-bold text-emerald-300">{counts.correct}</td>
                        <td className="py-2 text-center font-bold text-rose-300">{counts.incorrect}</td>
                        <td className="py-2 text-center text-slate-400">{counts.unverified}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-[11px] text-slate-400">
                Reveals whether student agreement correlates with verified statistical accuracy.
              </p>
            </div>
          </div>
        )}
      </Card>

      {/* 6. Error Analysis: Key Segments & Top Residuals */}
      <Card
        title={`Error Analysis & Cohort Discrepancies (n=${errorsData?.n || 0})`}
        subtitle="Identifies common confusion patterns across lifestyle segments."
      >
        {errorsData?.n === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            Not yet established (n=0). Awaiting error records.
          </div>
        ) : (
          <div className="space-y-6">
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20">
                <span className="text-[10px] font-bold text-rose-300 uppercase tracking-wider block">
                  False Positives (Predicted High, True Low)
                </span>
                <span className="text-2xl font-black text-rose-400 mt-1 block">
                  {errorsData?.false_positives_count}
                  <small className="text-xs text-slate-400 font-normal ml-1">
                    ({((errorsData?.fp_rate || 0) * 100).toFixed(1)}% rate)
                  </small>
                </span>
              </div>
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
                <span className="text-[10px] font-bold text-amber-300 uppercase tracking-wider block">
                  False Negatives (Missed High Risk)
                </span>
                <span className="text-2xl font-black text-amber-400 mt-1 block">
                  {errorsData?.false_negatives_count}
                  <small className="text-xs text-slate-400 font-normal ml-1">
                    ({((errorsData?.fn_rate || 0) * 100).toFixed(1)}% rate)
                  </small>
                </span>
              </div>
            </div>

            {/* Segment Breakdown */}
            <div>
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
                Segment Error Rates:
              </h4>
              <div className="grid sm:grid-cols-3 gap-3">
                {Object.entries(errorsData?.segments || {}).map(([key, seg]) => (
                  <div key={key} className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
                    <span className="text-xs font-semibold text-white block">{seg.name}</span>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Accuracy:</span>
                      <span className="font-bold text-teal-300">{seg.accuracy_pct}%</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Samples:</span>
                      <span className="text-slate-300">n = {seg.n}</span>
                    </div>
                    {seg.low_sample_flag && (
                      <span className="inline-block text-[10px] text-amber-400 font-semibold mt-1">
                        ⚠️ Low sample (n &lt; 5)
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* 7. Model Version History with Promote & Rollback */}
      <Card
        title="Model Version History & Controlled Rollback"
        subtitle="Candidate models are evaluated strictly on the frozen held-out test set (n=27). v1.0 is permanently preserved."
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-white/10 text-slate-400">
              <tr>
                <th className="pb-2">Version</th>
                <th className="pb-2">Status</th>
                <th className="pb-2">Parent</th>
                <th className="pb-2">Training Rows</th>
                <th className="pb-2">Registered Date</th>
                <th className="pb-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-slate-200">
              {modelsData?.models?.map((m) => (
                <tr key={m.version}>
                  <td className="py-3 font-bold text-white flex items-center gap-2">
                    <span>{m.version}</span>
                    {m.version === 'v1.0' && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-teal-500/20 text-teal-300 uppercase font-black">
                        Baseline
                      </span>
                    )}
                  </td>
                  <td className="py-3">
                    {m.is_active ? (
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold">
                        ACTIVE
                      </span>
                    ) : (
                      <span className="text-slate-500 text-[10px]">INACTIVE</span>
                    )}
                  </td>
                  <td className="py-3 text-slate-400">{m.parent || 'None (Genesis)'}</td>
                  <td className="py-3">{m.training_rows}</td>
                  <td className="py-3 text-slate-400">{m.created_at?.slice(0, 10)}</td>
                  <td className="py-3 text-right">
                    {!m.is_active && (
                      <button
                        onClick={() => handleRollback(m.version)}
                        disabled={retrainingLoading}
                        className="px-3 py-1 rounded-lg bg-white/10 hover:bg-white/15 text-white font-semibold text-[11px] transition-all"
                      >
                        Rollback to {m.version}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* 8. Methodology & Limitations Note */}
      <Card
        title="Validation Methodology & Audit Safeguards"
        subtitle="How SmartPulse ensures zero data fabrication and non-leaking evaluation."
      >
        <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
          <p>
            • <strong>Frozen Held-Out Isolation:</strong> The 27-student held-out test set (20% of original cohort, stratified seed=42) is permanently frozen and locked against training or hyperparameter tuning. Candidates must beat the active model on this exact frozen test set.
          </p>
          <p>
            • <strong>Non-Clinical Scope:</strong> Predictions represent statistical academic likelihoods derived from convenience sample survey data, not psychological diagnosis.
          </p>
          <p>
            • <strong>Subjective vs Ground Truth:</strong> Feedback ratings (Yes/No/Not sure) reflect self-perception and are never treated as actual values in accuracy metrics or retraining. Only verified 5-item burnout battery actuals serve as ground truth.
          </p>
          <p>
            • <strong>Rigorous Confidence Intervals:</strong> Proportions use the Wilson score interval to handle skewed small-sample behavior. Regression metrics utilize 1,000 bootstrap resamples.
          </p>
        </div>
      </Card>

      <Disclaimer />
    </PageTransition>
  );
}
