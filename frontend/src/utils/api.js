/**
 * SmartPulse Centralized API Client
 */

const API_BASE = '/api';

export async function fetchOverview() {
  const res = await fetch(`${API_BASE}/overview`);
  if (!res.ok) throw new Error(`Failed to load overview data: ${res.statusText}`);
  return res.json();
}

export async function predictCategory(payload) {
  const res = await fetch(`${API_BASE}/predict/category`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail?.[0]?.msg || 'Failed to predict burnout category');
  }
  return res.json();
}

export async function predictScore(payload) {
  const res = await fetch(`${API_BASE}/predict/score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail?.[0]?.msg || 'Failed to predict continuous score');
  }
  return res.json();
}

export async function explainPrediction(payload) {
  const res = await fetch(`${API_BASE}/explain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail?.[0]?.msg || 'Failed to generate feature attributions');
  }
  return res.json();
}

export async function simulateWhatIf(baseline, modified) {
  const res = await fetch(`${API_BASE}/whatif`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ baseline, modified }),
  });
  if (!res.ok) throw new Error('Failed to run what-if simulation');
  return res.json();
}

export async function fetchInsights() {
  const res = await fetch(`${API_BASE}/stats/insights`);
  if (!res.ok) throw new Error('Failed to fetch statistical insights');
  return res.json();
}

export async function fetchPerformance() {
  const res = await fetch(`${API_BASE}/model/performance`);
  if (!res.ok) throw new Error('Failed to fetch model evaluation metrics');
  return res.json();
}

export async function downloadReportPdf(payload) {
  const res = await fetch(`${API_BASE}/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to generate PDF report');
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `SmartPulse_Report_${new Date().toISOString().slice(0, 10)}.pdf`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
