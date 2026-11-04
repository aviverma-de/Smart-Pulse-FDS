import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { Users, Flame, Activity, Moon, TrendingUp, Lightbulb, ClipboardCheck, BrainCircuit, ChartNoAxesColumn, Leaf, ArrowRight, RefreshCw } from 'lucide-react';
import PageTransition from '../components/PageTransition';
import { fetchOverview } from '../utils/api';

const shortcuts = [
  { to: '/assessment', title: 'Take Assessment', copy: 'Fill a short questionnaire about your academic habits and lifestyle.', icon: ClipboardCheck, tone: 'blue' },
  { to: '/predictions', title: 'Get AI Predictions', copy: 'Predict your burnout category and estimated burnout score.', icon: BrainCircuit, tone: 'violet' },
  { to: '/report', title: 'Explore Insights', copy: 'View key statistical findings from our analysis.', icon: ChartNoAxesColumn, tone: 'green' },
  { to: '/recommendations', title: 'Personalized Recommendations', copy: 'Get actionable suggestions for a healthier academic life.', icon: Leaf, tone: 'gold' },
];

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const loadData = () => {
    setLoading(true); setError('');
    fetchOverview().then(setData).catch((err) => setError(err.message)).finally(() => setLoading(false));
  };
  useEffect(() => { loadData(); }, []);

  const timeline = data?.stress_timeline || [];
  const beginning = timeline[0]?.mean ?? 1.97;
  const middle = timeline[1]?.mean ?? 3.06;
  const current = timeline[2]?.mean ?? 3.20;
  const increase = (((middle - beginning) / beginning) * 100).toFixed(1);

  return (
    <PageTransition className="dashboard-page">
      <header className="dashboard-header">
        <div><div className="eyebrow">DATA-DRIVEN INSIGHTS FOR A HEALTHIER ACADEMIC JOURNEY</div>
          <h1>Welcome to <span>SmartPulse</span></h1>
          <p>Understand your well-being, predict burnout and take control with data-driven insights.</p></div>
        <div className="header-actions"><Link className="primary-button" to="/assessment">Take a New Assessment <ArrowRight /></Link></div>
      </header>

      {loading ? <div className="dashboard-state">Loading student well-being insights…</div> : error ? <div className="dashboard-state error-state"><span>{error}</span><button onClick={loadData}><RefreshCw /> Retry</button></div> : data && <>
        <section className="metric-grid" aria-label="Cohort overview">
          <Metric icon={Users} tone="blue" label="Students Surveyed" value={data.n_students ?? 132} />
          <Metric icon={Flame} tone="red" label="Avg. Burnout Score" value={Number(data.mean_burnout ?? 14.98).toFixed(2)} suffix="/ 25" />
          <Metric icon={Activity} tone="green" label="Avg. Stress Score" value={Number(data.mean_stress ?? 11.66).toFixed(2)} suffix="/ 20" />
          <Metric icon={Moon} tone="purple" label="Avg. Sleep Duration" value={Number(data.mean_sleep ?? 6.55).toFixed(2)} suffix="hrs" />
        </section>

        <section className="insight-grid">
          <article className="surface-card chart-card">
            <div className="panel-heading"><div><TrendingUp /><div><h2>Stress Across Semester Stages</h2><p>Mean reported stress score at different stages of the semester.</p></div></div></div>
            <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><AreaChart data={timeline} margin={{ top: 14, right: 14, left: 0, bottom: 4 }}>
              <defs><linearGradient id="stressFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#4e91ef" stopOpacity={0.28} /><stop offset="100%" stopColor="#4e91ef" stopOpacity={0.04} /></linearGradient></defs>
              <CartesianGrid vertical={false} stroke="#e8edf4" /><XAxis dataKey="stage" tickLine={false} axisLine={{ stroke: '#aeb8c6' }} tick={{ fill: '#49566d', fontSize: 12 }} /><YAxis domain={[0, 5]} ticks={[0, 1, 2, 3, 4, 5]} tickLine={false} axisLine={{ stroke: '#aeb8c6' }} tick={{ fill: '#667085', fontSize: 12 }} />
              <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #e5eaf1', color: '#14213d' }} formatter={(value) => [`${Number(value).toFixed(2)} / 5`, 'Mean stress']} />
              <Area type="monotone" dataKey="mean" stroke="#438bea" strokeWidth={2.5} fill="url(#stressFill)" dot={{ r: 5, fill: '#438bea', stroke: '#fff', strokeWidth: 2 }} activeDot={{ r: 7 }} />
            </AreaChart></ResponsiveContainer></div>
          </article>
          <article className="surface-card key-insight">
            <div className="panel-heading insight-heading"><div><Lightbulb /><h2>Key Insight</h2></div><span className="pill">Semester Trend</span></div>
            <div className="big-insight">{increase}%</div><h3>increase in stress from the beginning<br className="wide-only" /> to the middle of the semester.</h3>
            <p>Students experience a substantial rise in stress during the first half of the semester, followed by a smaller increase towards the current stage.</p>
            <div className="note-box"><span>i</span><div>Based on responses from {data.n_students} students.<br />Stress measured on a 5-point scale.</div></div>
          </article>
        </section>

        <section className="explore-section"><h2>Explore <span>SmartPulse</span></h2><div className="shortcut-grid">{shortcuts.map(({ to, title, copy, icon: Icon, tone }) => <Link className={`shortcut-card ${tone}`} to={to} key={title}><div className="shortcut-content"><Icon /><div><h3>{title}</h3><p>{copy}</p></div></div><span className="shortcut-arrow"><ArrowRight /></span></Link>)}</div></section>
      </>}
    </PageTransition>
  );
}

function Metric({ icon: Icon, tone, label, value, suffix }) {
  return <article className="surface-card metric-card"><div className={`metric-icon ${tone}`}><Icon /></div><div className="metric-copy"><span>{label}</span><strong>{value} <small>{suffix}</small></strong></div></article>;
}
