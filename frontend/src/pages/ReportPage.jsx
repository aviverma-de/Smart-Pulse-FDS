import React, { useState, useEffect } from 'react';
import { Download, FileText, CheckCircle2, ShieldCheck, Printer, Calendar, User } from 'lucide-react';
import PageTransition from '../components/PageTransition';
import Card from '../components/Card';
import RiskBadge from '../components/RiskBadge';
import Disclaimer from '../components/Disclaimer';
import { downloadReportPdf } from '../utils/api';
import { DEFAULT_ASSESSMENT } from '../utils/constants';

export default function ReportPage() {
  const [data, setData] = useState(null);
  const [studentName, setStudentName] = useState('Student');
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const cached = sessionStorage.getItem('smartpulse_assessment');
    if (cached) {
      try {
        setData(JSON.parse(cached));
      } catch (e) {
        console.error(e);
      }
    } else {
      setData({
        inputs: DEFAULT_ASSESSMENT,
        prediction: { category: 'High Risk', probabilities: { high: 0.63, low: 0.37 }, model_used: 'Random Forest' },
        score: { predicted_score: 16.5, credible_interval_94: [11.2, 19.8], percentile: 68.2, calculated_stress_total: 13 },
        explanation: {
          method: 'Logistic Regression log-odds decomposition',
          top_factors: [
            { label: 'Perceived Workload', impact_level: 'High Impact', explanation: 'Reported heavy workload is the strongest correlate with high burnout.' },
            { label: 'Bedtime Phone Use', impact_level: 'High Impact', explanation: 'Daily smartphone use in bed before sleep elevates mental fatigue.' }
          ]
        }
      });
    }
  }, []);

  const handleDownload = async () => {
    if (!data) return;
    setDownloading(true);
    try {
      const payload = {
        inputs: data.inputs,
        prediction: data.prediction,
        score: data.score,
        explanation: data.explanation,
        student_name: studentName.trim() || 'Student',
        opt_in_storage: false,
      };
      await downloadReportPdf(payload);
    } catch (err) {
      console.error(err);
      alert('Could not download PDF report. Ensure backend is running.');
    } finally {
      setDownloading(false);
    }
  };

  if (!data) return null;

  const { inputs, prediction, score, explanation } = data;
  const isHigh = prediction?.category === 'High Risk';

  return (
    <PageTransition className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-teal-400 uppercase tracking-wider mb-1">
            <span>Official Course Summary Document</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Wellness Assessment Report
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Downloadable clinical-disclaimed PDF summary for personal tracking and advisory review.
          </p>
        </div>

        <button
          onClick={handleDownload}
          disabled={downloading}
          className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold text-xs sm:text-sm shadow-lg shadow-teal-500/20 transition-all hover:scale-105 disabled:opacity-50 self-start sm:self-auto"
        >
          <Download className="w-4 h-4" />
          <span>{downloading ? 'Compiling PDF...' : 'Download PDF Report'}</span>
        </button>
      </div>

      {/* Name Customization Row */}
      <div className="p-4 rounded-xl bg-white/[0.02] border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-slate-300">
          <User className="w-4 h-4 text-teal-400" />
          <span>Name on Document:</span>
          <input
            type="text"
            value={studentName}
            onChange={(e) => setStudentName(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white text-xs focus:outline-none focus:border-teal-400"
            placeholder="Your name / ID"
          />
        </div>
        <div className="flex items-center gap-2 text-slate-400">
          <Calendar className="w-4 h-4 text-slate-500" />
          <span>Date: {new Date().toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}</span>
        </div>
      </div>

      {/* Clean Document Preview Card */}
      <div className="glass-panel rounded-2xl p-6 sm:p-10 border border-white/15 space-y-8 bg-white/[0.02] relative">
        {/* Document Header Preview */}
        <div className="border-b border-white/10 pb-6">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xl font-extrabold text-white tracking-tight">SmartPulse</span>
              <p className="text-xs text-teal-400 font-medium">Understand stress. Predict burnout. Take action.</p>
            </div>
            <div className="text-right text-xs text-slate-400 font-mono">
              Report ID: SP-{Date.now().toString().slice(-6)}
            </div>
          </div>
        </div>

        {/* Executive Summary Row */}
        <div className="grid sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Predicted Category</span>
            <div><RiskBadge category={prediction?.category} size="md" /></div>
            <p className="text-[11px] text-slate-400 mt-1">
              Prob: {((prediction?.probabilities?.high || 0.5) * 100).toFixed(1)}% High
            </p>
          </div>

          <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Estimated Burnout Score</span>
            <div className="text-2xl font-extrabold text-white font-mono">
              {score?.predicted_score?.toFixed(1) || '15.0'} <span className="text-xs text-slate-400 font-normal">/ 25</span>
            </div>
            <p className="text-[11px] text-teal-400">
              94% HDI: [{score?.credible_interval_94?.[0]?.toFixed(1) || '10.2'}, {score?.credible_interval_94?.[1]?.toFixed(1) || '18.8'}]
            </p>
          </div>

          <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Cohort Standing</span>
            <div className="text-2xl font-extrabold text-cyan-300 font-mono">
              {score?.percentile?.toFixed(0) || '50'}th <span className="text-xs text-slate-400 font-normal">percentile</span>
            </div>
            <p className="text-[11px] text-slate-400">
              PSS-4 Stress Total: {score?.calculated_stress_total || '12'} / 20
            </p>
          </div>
        </div>

        {/* Survey Inputs Table Preview */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Reported Lifestyle Factors
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5">
              <span className="text-slate-500 block text-[10px]">Sleep Hours</span>
              <span className="font-semibold text-slate-200">{inputs?.sleep_mid_hrs} hrs/night</span>
            </div>
            <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5">
              <span className="text-slate-500 block text-[10px]">Sleep Quality</span>
              <span className="font-semibold text-slate-200">{inputs?.sleep_quality} / 5 scale</span>
            </div>
            <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5">
              <span className="text-slate-500 block text-[10px]">Workload Code</span>
              <span className="font-semibold text-slate-200">{inputs?.workload_code} / 4 scale</span>
            </div>
            <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5">
              <span className="text-slate-500 block text-[10px]">Bedtime Phone Use</span>
              <span className="font-semibold text-slate-200">{inputs?.phone_bed_code} / 4 code</span>
            </div>
            <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5">
              <span className="text-slate-500 block text-[10px]">Exercise</span>
              <span className="font-semibold text-slate-200">{inputs?.exercise_days_mid} days/wk</span>
            </div>
            <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5">
              <span className="text-slate-500 block text-[10px]">Deadlines</span>
              <span className="font-semibold text-slate-200">{inputs?.deadlines_code} / 4 code</span>
            </div>
            <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5">
              <span className="text-slate-500 block text-[10px]">Bedtime</span>
              <span className="font-semibold text-slate-200">{inputs?.bedtime_code} / 4 code</span>
            </div>
            <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5">
              <span className="text-slate-500 block text-[10px]">Exam Performance</span>
              <span className="font-semibold text-slate-200">{inputs?.performance_code ? `${inputs.performance_code} / 5` : 'No exams yet'}</span>
            </div>
          </div>
        </div>

        {/* Top Attributions Preview */}
        <div className="space-y-3 pt-2">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Key Statistical Drivers (Attribution Analysis)
          </h4>
          <div className="space-y-2">
            {explanation?.top_factors?.slice(0, 3).map((tf, i) => (
              <div key={i} className="p-3 rounded-lg bg-white/[0.02] border border-white/5 text-xs text-slate-300">
                <span className="font-bold text-white">{tf.label}: </span>
                <span>{tf.explanation}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <Disclaimer />
    </PageTransition>
  );
}
