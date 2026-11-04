import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Check, Sparkles, Moon, Smartphone, GraduationCap, HeartPulse } from 'lucide-react';
import PageTransition from '../components/PageTransition';
import Card from '../components/Card';
import Disclaimer from '../components/Disclaimer';
import {
  SLEEP_OPTIONS,
  SLEEP_QUALITY_OPTIONS,
  BEDTIME_OPTIONS,
  SCREEN_OPTIONS,
  PHONE_BED_OPTIONS,
  EXERCISE_OPTIONS,
  DEADLINES_OPTIONS,
  WORKLOAD_OPTIONS,
  PERFORMANCE_OPTIONS,
  PSS_OPTIONS,
  DEFAULT_ASSESSMENT
} from '../utils/constants';
import { predictCategory, predictScore, explainPrediction } from '../utils/api';

export default function AssessmentPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState(DEFAULT_ASSESSMENT);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const totalSteps = 4;

  const handleChange = (field, val) => {
    setFormData((prev) => ({
      ...prev,
      [field]: val,
    }));
  };

  const handleNext = () => {
    setError(null);
    if (step < totalSteps) {
      setStep(step + 1);
    }
  };

  const handlePrev = () => {
    setError(null);
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      // Execute category prediction, continuous score estimation, and attribution in parallel
      const [categoryRes, scoreRes, explainRes] = await Promise.all([
        predictCategory(formData),
        predictScore(formData),
        explainPrediction(formData),
      ]);

      const assessmentResults = {
        inputs: formData,
        prediction: categoryRes,
        score: scoreRes,
        explanation: explainRes,
        timestamp: new Date().toISOString(),
      };

      // Store in sessionStorage for persistence across pages
      sessionStorage.setItem('smartpulse_assessment', JSON.stringify(assessmentResults));

      navigate('/predictions', { state: assessmentResults });
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to analyze assessment. Please ensure backend is running.');
      setSubmitting(false);
    }
  };

  const stepTitles = [
    { num: 1, title: 'Sleep & Nightly Habits', icon: Moon },
    { num: 2, title: 'Screen Time & Smartphone Habits', icon: Smartphone },
    { num: 3, title: 'Academic Pressure & Exercise', icon: GraduationCap },
    { num: 4, title: 'Perceived Stress Scale (PSS-4)', icon: HeartPulse },
  ];

  return (
    <PageTransition className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      {/* Top Header */}
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold text-teal-400 uppercase tracking-wider mb-1">
          <span>Student Well-Being Questionnaire</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Lifestyle & Academic Pressure Assessment
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Step {step} of {totalSteps}: Answer honestly. Responses are processed locally in-memory.
        </p>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden p-0.5 border border-white/10">
          <div
            className="h-full bg-gradient-to-r from-teal-500 to-cyan-400 rounded-full transition-all duration-300"
            style={{ width: `${(step / totalSteps) * 100}%` }}
          />
        </div>
        <div className="grid grid-cols-4 gap-2 text-center">
          {stepTitles.map((s) => {
            const Icon = s.icon;
            const isCurrent = s.num === step;
            const isCompleted = s.num < step;
            return (
              <div
                key={s.num}
                className={`flex flex-col items-center gap-1 text-[11px] font-medium transition-all ${
                  isCurrent
                    ? 'text-teal-300 font-bold'
                    : isCompleted
                    ? 'text-slate-400'
                    : 'text-slate-600'
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                    isCurrent
                      ? 'bg-teal-500 text-slate-950 font-bold'
                      : isCompleted
                      ? 'bg-teal-500/20 text-teal-400 border border-teal-500/30'
                      : 'bg-white/5 text-slate-500'
                  }`}
                >
                  {isCompleted ? <Check className="w-3.5 h-3.5" /> : s.num}
                </div>
                <span className="hidden sm:inline">{s.title.split(' ')[0]}</span>
              </div>
            );
          })}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
          <b>Error:</b> {error}
        </div>
      )}

      {/* Form Card */}
      <form onSubmit={handleSubmit}>
        <Card className="p-6 sm:p-8 space-y-6">
          {/* STEP 1: SLEEP */}
          {step === 1 && (
            <div className="space-y-6 animate-in fade-in duration-200">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Moon className="w-5 h-5 text-teal-400" />
                <span>Sleep Duration & Bedtime Schedule</span>
              </h2>

              {/* Sleep Hours */}
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Typical Nightly Sleep Duration
                </label>
                <select
                  value={formData.sleep_mid_hrs}
                  onChange={(e) => handleChange('sleep_mid_hrs', parseFloat(e.target.value))}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-teal-400 transition-colors"
                >
                  {SLEEP_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value} className="bg-[#0F172A] text-white">
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Sleep Quality */}
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Subjective Sleep Quality (1 to 5)
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-5 gap-2">
                  {SLEEP_QUALITY_OPTIONS.map((opt) => (
                    <button
                      type="button"
                      key={opt.value}
                      onClick={() => handleChange('sleep_quality', opt.value)}
                      className={`p-3 rounded-xl text-left border text-xs transition-all ${
                        formData.sleep_quality === opt.value
                          ? 'bg-teal-500/20 border-teal-500 text-teal-300 shadow-sm'
                          : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10'
                      }`}
                    >
                      <div className="font-bold">{opt.label.split('—')[0]}</div>
                      <div className="text-[10px] text-slate-400 mt-1">{opt.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Typical Bedtime */}
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Typical Bedtime
                </label>
                <select
                  value={formData.bedtime_code}
                  onChange={(e) => handleChange('bedtime_code', parseInt(e.target.value, 10))}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-teal-400 transition-colors"
                >
                  {BEDTIME_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value} className="bg-[#0F172A] text-white">
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* STEP 2: SCREEN TIME & PHONE */}
          {step === 2 && (
            <div className="space-y-6 animate-in fade-in duration-200">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Smartphone className="w-5 h-5 text-cyan-400" />
                <span>Screen Exposure & Bedtime Smartphone Usage</span>
              </h2>

              {/* Screen Hours */}
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Daily Non-Academic Screen Time
                </label>
                <select
                  value={formData.screen_mid_hrs}
                  onChange={(e) => handleChange('screen_mid_hrs', parseFloat(e.target.value))}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-teal-400 transition-colors"
                >
                  {SCREEN_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value} className="bg-[#0F172A] text-white">
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Phone in Bed */}
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  How often do you use your smartphone in bed directly before sleep?
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {PHONE_BED_OPTIONS.map((opt) => (
                    <button
                      type="button"
                      key={opt.value}
                      onClick={() => handleChange('phone_bed_code', opt.value)}
                      className={`p-4 rounded-xl text-left border text-xs transition-all ${
                        formData.phone_bed_code === opt.value
                          ? 'bg-cyan-500/20 border-cyan-500 text-cyan-200 shadow-sm'
                          : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10'
                      }`}
                    >
                      <div className="font-bold text-sm text-white">{opt.label}</div>
                      <div className="text-[11px] text-slate-400 mt-1">{opt.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: WORKLOAD, EXERCISE, DEADLINES, PERFORMANCE */}
          {step === 3 && (
            <div className="space-y-6 animate-in fade-in duration-200">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-amber-400" />
                <span>Academic Pressure & Lifestyle Balance</span>
              </h2>

              {/* Perceived Workload */}
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Perceived Academic Study Workload
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {WORKLOAD_OPTIONS.map((opt) => (
                    <button
                      type="button"
                      key={opt.value}
                      onClick={() => handleChange('workload_code', opt.value)}
                      className={`p-4 rounded-xl text-left border text-xs transition-all ${
                        formData.workload_code === opt.value
                          ? 'bg-amber-500/20 border-amber-500 text-amber-200 shadow-sm'
                          : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10'
                      }`}
                    >
                      <div className="font-bold text-sm text-white">{opt.label}</div>
                      <div className="text-[11px] text-slate-400 mt-1">{opt.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Exercise Days */}
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Physical Exercise / Activity (Days per week)
                </label>
                <select
                  value={formData.exercise_days_mid}
                  onChange={(e) => handleChange('exercise_days_mid', parseFloat(e.target.value))}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-teal-400 transition-colors"
                >
                  {EXERCISE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value} className="bg-[#0F172A] text-white">
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Deadlines */}
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Upcoming Academic Deadlines (Next 2 Weeks)
                </label>
                <select
                  value={formData.deadlines_code}
                  onChange={(e) => handleChange('deadlines_code', parseInt(e.target.value, 10))}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-teal-400 transition-colors"
                >
                  {DEADLINES_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value} className="bg-[#0F172A] text-white">
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Performance vs Expectations */}
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Recent Exam Performance Relative to Expectations
                </label>
                <select
                  value={formData.performance_code ?? 'none'}
                  onChange={(e) => {
                    const val = e.target.value === 'none' ? null : parseFloat(e.target.value);
                    handleChange('performance_code', val);
                  }}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-teal-400 transition-colors"
                >
                  {PERFORMANCE_OPTIONS.map((opt, i) => (
                    <option
                      key={i}
                      value={opt.value === null ? 'none' : opt.value}
                      className="bg-[#0F172A] text-white"
                    >
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* STEP 4: PERCEIVED STRESS SCALE (PSS-4) */}
          {step === 4 && (
            <div className="space-y-6 animate-in fade-in duration-200">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <HeartPulse className="w-5 h-5 text-rose-400" />
                  <span>Perceived Stress Items (PSS-4 Scale)</span>
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  These responses calculate your baseline stress total (not used as input features to prevent target leakage in ML models).
                </p>
              </div>

              {/* PSS Item 1 */}
              <div className="space-y-2 border-b border-white/5 pb-4">
                <label className="block text-xs font-medium text-slate-200">
                  1. In the last month, how often have you felt unable to control the important things in your life?
                </label>
                <div className="flex flex-wrap gap-2">
                  {PSS_OPTIONS.map((opt) => (
                    <button
                      type="button"
                      key={opt.value}
                      onClick={() => handleChange('pss1_no_control', opt.value)}
                      className={`px-3 py-1.5 rounded-lg border text-xs transition-all ${
                        formData.pss1_no_control === opt.value
                          ? 'bg-rose-500/20 border-rose-500 text-rose-200 font-bold'
                          : 'bg-white/5 border-white/10 text-slate-400 hover:text-white'
                      }`}
                    >
                      {opt.value} — {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* PSS Item 2 */}
              <div className="space-y-2 border-b border-white/5 pb-4">
                <label className="block text-xs font-medium text-slate-200">
                  2. In the last month, how often have you felt confident about your ability to handle your personal problems?
                </label>
                <div className="flex flex-wrap gap-2">
                  {PSS_OPTIONS.map((opt) => (
                    <button
                      type="button"
                      key={opt.value}
                      onClick={() => handleChange('pss2_confident', opt.value)}
                      className={`px-3 py-1.5 rounded-lg border text-xs transition-all ${
                        formData.pss2_confident === opt.value
                          ? 'bg-rose-500/20 border-rose-500 text-rose-200 font-bold'
                          : 'bg-white/5 border-white/10 text-slate-400 hover:text-white'
                      }`}
                    >
                      {opt.value} — {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* PSS Item 3 */}
              <div className="space-y-2 border-b border-white/5 pb-4">
                <label className="block text-xs font-medium text-slate-200">
                  3. In the last month, how often have you felt that things were going your way?
                </label>
                <div className="flex flex-wrap gap-2">
                  {PSS_OPTIONS.map((opt) => (
                    <button
                      type="button"
                      key={opt.value}
                      onClick={() => handleChange('pss3_going_my_way', opt.value)}
                      className={`px-3 py-1.5 rounded-lg border text-xs transition-all ${
                        formData.pss3_going_my_way === opt.value
                          ? 'bg-rose-500/20 border-rose-500 text-rose-200 font-bold'
                          : 'bg-white/5 border-white/10 text-slate-400 hover:text-white'
                      }`}
                    >
                      {opt.value} — {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* PSS Item 4 */}
              <div className="space-y-2">
                <label className="block text-xs font-medium text-slate-200">
                  4. In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?
                </label>
                <div className="flex flex-wrap gap-2">
                  {PSS_OPTIONS.map((opt) => (
                    <button
                      type="button"
                      key={opt.value}
                      onClick={() => handleChange('pss4_piling_up', opt.value)}
                      className={`px-3 py-1.5 rounded-lg border text-xs transition-all ${
                        formData.pss4_piling_up === opt.value
                          ? 'bg-rose-500/20 border-rose-500 text-rose-200 font-bold'
                          : 'bg-white/5 border-white/10 text-slate-400 hover:text-white'
                      }`}
                    >
                      {opt.value} — {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex items-center justify-between pt-6 border-t border-white/10">
            {step > 1 ? (
              <button
                type="button"
                onClick={handlePrev}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-semibold border border-white/10 transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Previous Step
              </button>
            ) : (
              <div />
            )}

            {step < totalSteps ? (
              <button
                type="button"
                onClick={handleNext}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-bold shadow-md shadow-teal-500/20 transition-all hover:scale-105"
              >
                <span>Continue</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center gap-2 px-8 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-400 hover:from-teal-400 hover:to-cyan-300 text-slate-950 text-xs sm:text-sm font-extrabold shadow-lg shadow-teal-500/25 transition-all hover:scale-105 disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4" />
                <span>{submitting ? 'Analyzing Responses...' : 'Analyze My Well-being'}</span>
              </button>
            )}
          </div>
        </Card>
      </form>

      <Disclaimer />
    </PageTransition>
  );
}
