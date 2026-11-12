import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import AssessmentPage from './pages/AssessmentPage';
import PredictionsPage from './pages/PredictionsPage';
import EstimatorPage from './pages/EstimatorPage';
import RecommendationsPage from './pages/RecommendationsPage';
import ReportPage from './pages/ReportPage';
import OutcomeCheckPage from './pages/OutcomeCheckPage';
import ValidationCenterPage from './pages/ValidationCenterPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Navbar />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/assessment" element={<AssessmentPage />} />
            <Route path="/predictions" element={<PredictionsPage />} />
            <Route path="/estimator" element={<EstimatorPage />} />
            <Route path="/outcome-check" element={<OutcomeCheckPage />} />
            <Route path="/validation" element={<ValidationCenterPage />} />
            <Route path="/recommendations" element={<RecommendationsPage />} />
            <Route path="/report" element={<ReportPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
