import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { HeartPulse, CheckCircle, Moon, Smartphone, BookOpen, BatteryCharging, ArrowRight, ShieldCheck, Heart, FileText, PhoneCall } from 'lucide-react';
import PageTransition from '../components/PageTransition';
import Card from '../components/Card';
import RiskBadge from '../components/RiskBadge';
import Disclaimer from '../components/Disclaimer';
import { DEFAULT_ASSESSMENT } from '../utils/constants';

export default function RecommendationsPage() {
  const [data, setData] = useState(null);

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
        prediction: { category: 'High Risk' },
        score: { predicted_score: 16.5 },
      });
    }
  }, []);

  if (!data) return null;

  const { inputs, prediction, score } = data;
  const isHigh = prediction?.category === 'High Risk';

  // Dynamic supportive rule-based wellness recommendations
  const recommendations = [];

  if (inputs.workload_code >= 3) {
    recommendations.push({
      category: 'Workload & Time Strategy',
      icon: BookOpen,
      title: 'Modular Task Deconstruction',
      advice:
        'Your reported workload is heavy or overwhelming. Statistical models indicate workload is the highest correlate with student exhaustion. Try timeboxing projects into 25-minute sprints (Pomodoro) and limit your primary daily task list to two key priorities.',
      tag: 'High Impact Factor',
      color: 'teal',
    });
  }

  if (inputs.phone_bed_code >= 3) {
    recommendations.push({
      category: 'Sleep Architecture & Devices',
      icon: Smartphone,
      title: 'Bedtime Device Distance',
      advice:
        'Frequent late-night phone browsing delays restorative slow-wave sleep. Consider placing your phone across the room 30 minutes before sleep and swapping screen scrolling for light reading or audio podcasts.',
      tag: 'Sleep Hygiene',
      color: 'cyan',
    });
  }

  if (inputs.sleep_mid_hrs <= 5.5 || inputs.sleep_quality <= 2) {
    recommendations.push({
      category: 'Rest & Recovery',
      icon: Moon,
      title: 'Consistent Circadian Anchoring',
      advice:
        'Sub-6 hour sleep cycles diminish cognitive resilience during exam periods. Aim to anchor a fixed wake-up time each morning, even on weekends, to stabilize your internal biological clock.',
      tag: 'Physiological Buffer',
      color: 'indigo',
    });
  }

  if (inputs.exercise_days_mid <= 1.5) {
    recommendations.push({
      category: 'Physical Resilience',
      icon: BatteryCharging,
      title: 'Low-Intensity Movement Breaks',
      advice:
        'Regular physical movement, even 15-minute campus walks between lecture halls, actively clears cortisol and promotes cognitive decompression.',
      tag: 'Stress Regulation',
      color: 'amber',
    });
  }

  // Baseline supportive recommendation
  recommendations.push({
    category: 'Social & Campus Well-Being',
    icon: Heart,
    title: 'Study Sabbaticals & Connection',
    advice:
      'Schedule non-negotiable downtime with friends or creative hobbies. Academic success is a marathon supported by emotional disengagement during off-hours.',
    tag: 'Community',
    color: 'emerald',
  });

  return (
    <PageTransition className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      {/* Title */}
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold text-teal-400 uppercase tracking-wider mb-1">
          <span>Evidence-Informed Student Well-Being Suggestions</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Personalized Wellness Recommendations
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Supportive, non-clinical lifestyle adaptations customized to your survey responses.
        </p>
      </div>

      {/* Gentle Counseling Box for High-Risk Results */}
      {isHigh && (
        <div className="p-6 rounded-2xl bg-gradient-to-r from-rose-500/15 via-rose-500/10 to-teal-500/10 border border-rose-500/30 text-slate-200 space-y-3 shadow-lg">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-rose-500/20 text-rose-300">
              <PhoneCall className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">
                Support is Always Available on Campus
              </h3>
              <p className="text-xs text-rose-300">
                You scored in the elevated burnout risk range ({score?.predicted_score?.toFixed(1) || '15+'} pts).
              </p>
            </div>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            University life can be demanding, and feeling stretched thin or exhausted is a shared experience among students. You don't have to navigate academic strain alone. We encourage reaching out to a trusted mentor, advisor, academic tutor, or your campus Student Counseling Center for confidential, friendly support.
          </p>
        </div>
      )}

      {/* Recommendations Cards */}
      <div className="space-y-4">
        {recommendations.map((rec, i) => {
          const Icon = rec.icon;
          return (
            <Card key={i} className="p-6">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-white/5 border border-white/10 text-teal-400 shrink-0">
                  <Icon className="w-5 h-5" />
                </div>
                <div className="space-y-2 flex-1">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      {rec.category}
                    </span>
                    <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-teal-500/10 text-teal-300 border border-teal-500/20 font-bold">
                      {rec.tag}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-white">{rec.title}</h3>
                  <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                    {rec.advice}
                  </p>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Action Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-white/10">
        <Link
          to="/report"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 text-xs font-bold shadow-md shadow-teal-500/20 transition-all hover:scale-105"
        >
          <FileText className="w-4 h-4" />
          <span>Generate Official PDF Wellness Report</span>
        </Link>
        <Link
          to="/estimator"
          className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white/10 hover:bg-white/15 text-white text-xs font-semibold border border-white/15 transition-all"
        >
          <span>Explore What-If Simulator</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      <Disclaimer />
    </PageTransition>
  );
}
