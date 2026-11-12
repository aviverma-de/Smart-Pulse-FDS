import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell, ReferenceLine } from 'recharts';
import { BrainCircuit, ArrowRight, ShieldCheck, HeartPulse, SlidersHorizontal, FileText, CheckCircle2, Copy, Check, Trash2, Send } from 'lucide-react';
import PageTransition from '../components/PageTransition';
import Card from '../components/Card';
import RiskBadge from '../components/RiskBadge';
import Disclaimer from '../components/Disclaimer';
import { submitFeedback, deleteStudentData } from '../utils/api';

export default function PredictionsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [data, setData] = useState(null);

  // Student feedback state
  const [agreement, setAgreement] = useState(null); // 'Yes' | 'No' | 'Not sure'
  const [scoreFeelsRight, setScoreFeelsRight] = useState(null);
  const [comment, setComment] = useState('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  // Return code and privacy state
  const [copiedCode, setCopiedCode] = useState(false);
  const [deletionMessage, setDeletionMessage] = useState(null);

  useEffect(() => {
    // Check location state first, then fallback to sessionStorage
    if (location.state?.prediction) {
      setData(location.state);
    } else {
      const cached = sessionStorage.getItem('smartpulse_assessment');
      if (cached) {
        try {
          setData(JSON.parse(cached));
        } catch (e) {
          console.error(e);
        }
      }
    }
  }, [location.state]);

  if (!data) {
    return (
      <PageTransition className="max-w-2xl mx-auto px-4 py-20 text-center space-y-6">
        <div className="w-14 h-14 rounded-2xl bg-teal-500/15 border border-teal-500/30 text-teal-400 flex items-center justify-center mx-auto">
          <BrainCircuit className="w-7 h-7" />
        </div>
        <h2 className="text-2xl font-bold text-white">No Assessment Data Found</h2>
        <p className="text-xs sm:text-sm text-slate-300 max-w-md mx-auto">
          Please complete the 9-item lifestyle questionnaire first so our machine learning models can evaluate your risk profile.
        </p>
        <Link
          to="/assessment"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all"
        >
          <span>Take Assessment</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </PageTransition>
    );
  }

  const { prediction, explanation, score } = data;
  const isHigh = prediction.category === 'High Risk';
  const probHigh = (prediction.probabilities?.high ?? 0.5) * 100;
  const probLow = (prediction.probabilities?.low ?? 0.5) * 100;

  const returnCode = prediction.return_code || sessionStorage.getItem('smartpulse_return_code');
  const anonId = prediction.anon_id || sessionStorage.getItem('smartpulse_anon_id');

  const probData = [
    { name: 'Low Risk', probability: Math.round(probLow * 10) / 10, fill: '#10B981' },
    { name: 'High Risk', probability: Math.round(probHigh * 10) / 10, fill: '#EF4444' },
  ];

  const contribData = (explanation.contributions || [])
    .slice(0, 8)
    .map((c) => ({
      feature: c.label,
      contribution: c.contribution,
      direction: c.direction,
    }));

  const handleCopyCode = () => {
    if (!returnCode) return;
    navigator.clipboard.writeText(returnCode);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const handleFeedbackSubmit = async (e) => {
    e.preventDefault();
    if (!agreement) return;
    setSubmittingFeedback(true);
    try {
      await submitFeedback({
        return_code: returnCode,
        prediction_id: prediction.prediction_id,
        agreement: agreement,
        score_feels_right: scoreFeelsRight,
        comment: comment.trim() || null,
      });
      setFeedbackSubmitted(true);
    } catch (err) {
      console.error('Feedback submission error:', err);
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const handleDeleteData = async () => {
    if (!anonId && !returnCode) return;
    if (!window.confirm('Are you sure you want to delete your anonymous research record? This cannot be undone.')) return;
    try {
      await deleteStudentData(anonId || returnCode);
      sessionStorage.removeItem('smartpulse_assessment');
      sessionStorage.removeItem('smartpulse_return_code');
      sessionStorage.removeItem('smartpulse_anon_id');
      setDeletionMessage('Your record and all associated predictions have been permanently deleted.');
    } catch (err) {
      alert(err.message || 'Failed to delete record.');
    }
  };

  return (
    <PageTransition className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      {/* Top Banner */}
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold text-teal-400 uppercase tracking-wider mb-1">
          <span>Machine Learning Risk Evaluation</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          AI Burnout Risk Prediction
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Model: {prediction.model_used} • Version: <span className="text-teal-300 font-bold">{prediction.model_version || 'v1.0'}</span>
        </p>
      </div>

      {deletionMessage && (
        <div className="p-4 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs">
          {deletionMessage}
        </div>
      )}

      {/* Main Results Hero Card */}
      <Card className="p-6 sm:p-8 border-teal-500/30 shadow-xl shadow-teal-500/5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-white/10">
          <div className="space-y-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Predicted Risk Status
            </span>
            <div className="flex items-center gap-3">
              <RiskBadge category={prediction.category} size="lg" />
              <span className="text-sm font-semibold text-slate-300">
                ({probHigh.toFixed(1)}% estimated risk)
              </span>
            </div>
            <p className="text-xs text-slate-300 max-w-lg leading-relaxed">
              {isHigh
                ? 'Your reported study habits, perceived academic workload, and sleep schedule align statistically with students in the elevated burnout risk group (≥ 15 sample median).'
                : 'Your current study habits and lifestyle balance align with students maintaining baseline stress tolerance (< 15 score).'}
            </p>
          </div>

          {/* Probabilities Mini-Display */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-4 sm:w-64 space-y-3 shrink-0">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Class Probabilities
            </div>
            {/* High bar */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300">High Risk</span>
                <span className="font-bold text-rose-400">{probHigh.toFixed(1)}%</span>
              </div>
              <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden">
                <div
                  className="h-full bg-rose-500 rounded-full transition-all duration-700"
                  style={{ width: `${probHigh}%` }}
                />
              </div>
            </div>
            {/* Low bar */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300">Low Risk</span>
                <span className="font-bold text-emerald-400">{probLow.toFixed(1)}%</span>
              </div>
              <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-700"
                  style={{ width: `${probLow}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Action Link row */}
        <div className="pt-6 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <CheckCircle2 className="w-4 h-4 text-teal-400" />
            <span>Classification Decision Threshold: 0.50 (OOF Repeated CV)</span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/estimator"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-teal-500/15 hover:bg-teal-500/25 border border-teal-500/30 text-teal-300 text-xs font-semibold transition-all"
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Score & What-If Simulator →</span>
            </Link>
            <Link
              to="/recommendations"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white/10 hover:bg-white/15 border border-white/15 text-white text-xs font-semibold transition-all"
            >
              <HeartPulse className="w-3.5 h-3.5" />
              <span>Recommendations</span>
            </Link>
          </div>
        </div>
      </Card>

      {/* STUDENT FEEDBACK CARD (Subjective, Not Ground Truth) */}
      <Card
        title="Student Feedback"
        subtitle="Help researchers calibrate our models. Labelled 'not ground truth' — never replaces verified actuals."
      >
        {!returnCode ? (
          <p className="text-xs text-slate-400">You did not opt in to anonymous research storage, so feedback is not stored.</p>
        ) : feedbackSubmitted ? (
          <div className="p-4 rounded-xl bg-teal-500/15 border border-teal-500/30 text-teal-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
            <span>Thank you for your feedback! It has been stored separately under subjective metrics.</span>
          </div>
        ) : (
          <form onSubmit={handleFeedbackSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-bold text-white block">
                How well does this describe your current condition?
              </label>
              <div className="flex gap-2">
                {['Yes', 'No', 'Not sure'].map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setAgreement(option)}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                      agreement === option
                        ? 'bg-teal-500 text-slate-950 font-bold'
                        : 'bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-white block">
                Does the predicted score feel about right? (Optional)
              </label>
              <div className="flex gap-2">
                {['Yes', 'No', 'Not sure'].map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setScoreFeelsRight(option)}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                      scoreFeelsRight === option
                        ? 'bg-teal-500 text-slate-950 font-bold'
                        : 'bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs text-slate-400 block">
                Optional comment:
              </label>
              <input
                type="text"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="e.g. My midterm schedule was unusually intense this week"
                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/15 text-white text-xs focus:outline-none focus:border-teal-500"
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-[10px] text-slate-400 italic">
                Subjective feedback — stored separately, not ground truth.
              </span>
              <button
                type="submit"
                disabled={!agreement || submittingFeedback}
                className="px-4 py-2 rounded-xl bg-teal-500 hover:bg-teal-400 disabled:opacity-50 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all flex items-center gap-1.5"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Submit Feedback</span>
              </button>
            </div>
          </form>
        )}
      </Card>

      {/* ANONYMOUS RETURN CODE & OUTCOME CHECK CARD */}
      {returnCode && <Card
        title="Follow-Up: Verified Burnout Outcome"
        subtitle="Independent verification is required to measure ground truth and improve models."
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-300 leading-relaxed">
            Your prediction has been registered with an anonymous return code. Later this semester (e.g. in 1-2 weeks), complete an independent 5-item burnout check to establish verified ground truth.
          </p>

          <div className="p-4 rounded-xl bg-white/5 border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                Your Anonymous Return Code
              </span>
              <code className="text-lg font-black text-teal-300 tracking-wider">{returnCode}</code>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleCopyCode}
                className="px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-xs text-white font-semibold flex items-center gap-1.5 transition-all"
              >
                {copiedCode ? <Check className="w-3.5 h-3.5 text-teal-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedCode ? 'Copied' : 'Copy Code'}</span>
              </button>
              <Link
                to="/outcome-check"
                className="px-4 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-1"
              >
                <span>Outcome Check →</span>
              </Link>
            </div>
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-white/10">
            <span>Want to delete your anonymous research record?</span>
            <button
              onClick={handleDeleteData}
              className="text-rose-400 hover:text-rose-300 underline flex items-center gap-1"
            >
              <Trash2 className="w-3 h-3" />
              <span>Delete My Record</span>
            </button>
          </div>
        </div>
      </Card>}

      {/* Why This Prediction? Attribution Section */}
      <Card
        title="Why this prediction? — Feature Contributions"
        subtitle={`Attribution Method: ${explanation.method || 'Logistic Regression log-odds decomposition'}`}
      >
        <p className="text-xs text-slate-300 mb-6 leading-relaxed">
          The chart below decomposes your responses into standardized log-odds risk contributions. Positive values (<span className="text-rose-400 font-semibold">red</span>) shift the model toward High Risk; negative values (<span className="text-emerald-400 font-semibold">green</span>) buffer against burnout.
        </p>

        {/* Feature Attribution Bar Chart */}
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              layout="vertical"
              data={contribData}
              margin={{ top: 10, right: 30, left: 40, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" horizontal={false} />
              <XAxis type="number" stroke="#94A3B8" fontSize={11} domain={[-1.2, 1.2]} />
              <YAxis
                type="category"
                dataKey="feature"
                stroke="#94A3B8"
                fontSize={11}
                tickLine={false}
                width={130}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0F172A',
                  borderColor: '#334155',
                  borderRadius: '12px',
                  color: '#F8FAFC',
                  fontSize: '12px',
                }}
                formatter={(val) => [`${val > 0 ? '+' : ''}${val.toFixed(3)} log-odds`, 'Contribution']}
              />
              <ReferenceLine x={0} stroke="#64748B" strokeWidth={1.5} />
              <Bar dataKey="contribution" radius={[0, 4, 4, 0]}>
                {contribData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.contribution >= 0 ? '#F43F5E' : '#10B981'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Plain Language Explanations per Top Factor */}
        <div className="mt-8 pt-6 border-t border-white/10 space-y-3">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Key Observed Drivers for Your Profile:
          </h4>
          <div className="grid sm:grid-cols-2 gap-3">
            {explanation.top_factors?.map((tf, i) => (
              <div
                key={i}
                className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">{tf.label}</span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                      tf.impact_level === 'High Impact'
                        ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                        : 'bg-teal-500/15 text-teal-300 border border-teal-500/30'
                    }`}
                  >
                    {tf.impact_level}
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">{tf.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      </Card>

      <Disclaimer />
    </PageTransition>
  );
}
