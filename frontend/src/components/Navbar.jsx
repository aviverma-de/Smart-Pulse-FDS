import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Activity, LayoutDashboard, ClipboardCheck, BrainCircuit, SlidersHorizontal, HeartHandshake, FileText, ChartNoAxesColumn } from 'lucide-react';

const navLinks = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/assessment', label: 'Assessment', icon: ClipboardCheck },
  { to: '/predictions', label: 'AI Prediction', icon: BrainCircuit },
  { to: '/estimator', label: 'What-if Simulator', icon: SlidersHorizontal },
  { to: '/report', label: 'Statistical Insights', icon: ChartNoAxesColumn },
  { to: '/predictions', label: 'Model Performance', icon: Activity },
  { to: '/recommendations', label: 'Recommendations', icon: HeartHandshake },
];

export default function Navbar() {
  return (
    <aside className="app-sidebar">
      <Link to="/dashboard" className="brand-lockup">
        <Activity className="brand-pulse" />
        <span><strong>SmartPulse</strong><small>Student Well-being Analytics</small></span>
      </Link>
      <nav className="side-nav" aria-label="Main navigation">
        {navLinks.map(({ to, label, icon: Icon }) => (
          <NavLink key={label} to={to} className={({ isActive }) => `side-link${isActive ? ' active' : ''}`}>
            <Icon aria-hidden="true" />{label}
          </NavLink>
        ))}
      </nav>
      <img className="sidebar-campus" src="/campus.jpg" alt="University campus buildings and green grounds" />
      <div className="sidebar-quote"><p>“A healthier student builds a brighter tomorrow.”</p><span /></div>
    </aside>
  );
}
