import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, AlertCircle, ArrowRight, ShieldCheck, HeartPulse, RefreshCw } from 'lucide-react';
import PageTransition from '../components/PageTransition';
import Card from '../components/Card';
import RiskBadge from '../components/RiskBadge';
import Disclaimer from '../components/Disclaimer';
import { submitOutcome } from '../utils/api';

const BO_QUESTIONS = [
  {
    id: 'bo1',
    label: '1. In the LAST 2 WEEKS, how often have you felt physically exhausted because of your studies?',
    description: 'Physical fatigue, body exhaustion, or low vitality directly linked to academic tasks.'
  },
  {
    id: 'bo2',
    label: '2. In the LAST 2 WEEKS, how often have you felt emotionally drained by college?',
    description: 'Feeling emotionally spent, overwhelmed, or unable to handle college stress.'
  },
  {
    id: 'bo3',
    label: '3. In the LAST 2 WEEKS, how often have you felt tired even after sleeping?',
    description: 'Waking up unrefreshed, persistent fatigue regardless of sleep length.'
  },
  {
    id: 'bo4',
    label: '4. In the LAST 2 WEEKS, how often have you felt you cannot cope with your studies anymore?',
    description: 'A sense of overload where coursework feels beyond your current coping threshold.'
  },
  {
    id: 'bo5',
    label: '5. In the LAST 2 WEEKS, how often have you felt less interested in your studies than before?',
    description: 'Drop in academic curiosity, apathy toward lectures, or reduced motivation.'
  }
];

const LIKERT_OPTIONS = [
  { val: 1, label: 'Never' },
  { val: 2, label: 'Rarely' },
  { val: 3, label: 'Sometimes' },
  { val: 4, label: 'Often' },
  { val: 5, label: 'Always' },
];

export default function OutcomeCheckPage() {
  const [returnCode, setReturnCode] = useState('');
  const [answers, setAnswers] = useState({ bo1: 3, bo2: 3, bo3: 3, bo4: 3, bo5: 3 });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    const cachedCode = sessionStorage.getItem('smartpulse_return_code');
    if (cachedCode) {
      setReturnCode(cachedCode);
    }
  }, []);

  const handleSelect = (qId, val) => {
    setAnswers(prev => ({ ...prev, [qId]: val }));
  };

  const currentScore = Object.values(answers).reduce((a, b) => a + b, 0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!returnCode.trim()) {
      setError('Please provide your anonymous return code.');
      return;
    }
    setSubmitting(true);
    setError(null);

    try {
      const res = await submitOutcome({
        return_code: returnCode.trim(),
        bo1: answers.bo1,
        bo2: answers.bo2,
        bo3: answers.bo3,
        bo4: answers.bo4,
        bo5: answers.bo5,
      });
      setResult(res);
    } catch (err) {
      setError(err.message || 'Failed to submit verified outcome.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PageTransition className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold text-teal-400 uppercase tracking-wider mb-1">
          <ShieldCheck className="w-4 h-4 text-teal-400" />
          <span>Independent Outcome Validation</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Verified Burnout Follow-Up Check
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Complete the exact 5-item burnout battery that defines the research study's ground truth.
          Predictor questions and outcome questions remain strictly isolated.
        </p>
      </div>

      {result ? (
        <Card className="p-6 sm:p-8 border-teal-500/30 text-center space-y-6">
          <div className="w-14 h-14 rounded-2xl bg-teal-500/15 border border-teal-500/30 text-teal-400 flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Outcome Verified & Recorded</h2>
            <p className="text-xs text-slate-400 mt-1">
              Your verified outcome has been saved for anonymous model performance tracking.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 max-w-md mx-auto space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Measured Burnout Score
              </span>
              <span className="text-2xl font-black text-white">
                {result.measured_score} <span className="text-xs text-slate-400">/ 25</span>
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Validated Risk Category
              </span>
              <RiskBadge category={result.measured_category} size="md" />
            </div>
            <div className="pt-2 border-t border-white/10 text-left text-[11px] text-slate-400 leading-relaxed">
              <strong>Ground-Truth Threshold:</strong> A score ≥ 15 (sample median) designates Elevated Burnout Risk.
              Only verified outcomes are used to measure model accuracy and train candidate models.
            </div>
          </div>

          <div className="flex justify-center gap-4 pt-4">
            <Link
              to="/validation"
              className="px-5 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all"
            >
              View Validation Center →
            </Link>
            <button
              onClick={() => setResult(null)}
              className="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-white font-semibold text-xs transition-all"
            >
              Check Another Code
            </button>
          </div>
        </Card>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Return Code Input Card */}
          <Card title="1. Your Anonymous Return Code" subtitle="Links your outcome to your initial prediction anonymously.">
            <div className="space-y-3">
              <input
                type="text"
                placeholder="e.g. SP-A1B2-C3D4"
                value={returnCode}
                onChange={(e) => setReturnCode(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/15 text-white font-mono text-sm tracking-wider uppercase focus:outline-none focus:border-teal-500"
                required
              />
              <p className="text-[11px] text-slate-400">
                You received this code on your assessment results page. If you lost it, take the assessment again to get a fresh code.
              </p>
            </div>
          </Card>

          {/* 5 Burnout Questions */}
          <Card
            title="2. Standard 5-Item Burnout Battery"
            subtitle="The exact psychological instrument used in the original research dataset (N=132)."
          >
            <div className="space-y-6">
              {BO_QUESTIONS.map((q) => (
                <div key={q.id} className="p-4 rounded-xl bg-white/[0.02] border border-white/5 space-y-3">
                  <div>
                    <h4 className="text-sm font-semibold text-white leading-snug">{q.label}</h4>
                    <p className="text-xs text-slate-400 mt-0.5">{q.description}</p>
                  </div>
                  <div className="grid grid-cols-5 gap-2">
                    {LIKERT_OPTIONS.map((opt) => (
                      <button
                        key={opt.val}
                        type="button"
                        onClick={() => handleSelect(q.id, opt.val)}
                        className={`py-2 px-1 rounded-lg text-xs font-semibold text-center transition-all ${
                          answers[q.id] === opt.val
                            ? 'bg-teal-500 text-slate-950 shadow-md font-bold'
                            : 'bg-white/5 text-slate-300 hover:bg-white/10 border border-white/10'
                        }`}
                      >
                        <span className="block text-base font-bold">{opt.val}</span>
                        <span className="text-[10px] opacity-80">{opt.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Live Score Preview */}
            <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-slate-400">
              <span>Live Calculated Score: <strong className="text-white text-sm">{currentScore} / 25</strong></span>
              <span>Category: <strong className={currentScore >= 15 ? 'text-rose-400' : 'text-emerald-400'}>{currentScore >= 15 ? 'High Risk (≥15)' : 'Low Risk (<15)'}</strong></span>
            </div>
          </Card>

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex justify-end gap-3">
            <Link
              to="/predictions"
              className="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-white font-semibold text-xs transition-all"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 disabled:opacity-50 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all flex items-center gap-2"
            >
              {submitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Submitting...</span>
                </>
              ) : (
                <>
                  <span>Submit Verified Outcome</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      )}

      <Disclaimer />
    </PageTransition>
  );
}
