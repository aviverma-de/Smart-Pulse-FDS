/**
 * SmartPulse Centralized API Client
 */

const API_BASE = '/api';

function getAdminHeaders(token) {
  const adminToken = token || localStorage.getItem('smartpulse_admin_token') || '';
  return {
    'Content-Type': 'application/json',
    'X-Admin-Token': adminToken,
  };
}

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

// ── Validation & Privacy Endpoints ──────────────────────────────────────────

export async function submitConsent(consent = true) {
  const res = await fetch(`${API_BASE}/consent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ consent }),
  });
  if (!res.ok) throw new Error('Failed to record consent');
  return res.json();
}

export async function deleteStudentData(anonId) {
  const res = await fetch(`${API_BASE}/data/${encodeURIComponent(anonId)}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete student record');
  return res.json();
}

export async function submitFeedback(payload) {
  const res = await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to record feedback');
  return res.json();
}

export async function submitOutcome(payload) {
  const res = await fetch(`${API_BASE}/outcome`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || 'Failed to submit verified outcome');
  }
  return res.json();
}

// ── Admin-Gated Validation API ──────────────────────────────────────────────

export async function fetchValidationSummary(includeDemo = false, token) {
  const res = await fetch(`${API_BASE}/validation/summary?include_demo=${includeDemo}`, {
    headers: getAdminHeaders(token),
  });
  if (!res.ok) {
    if (res.status === 401) throw new Error('ADMIN_AUTH_REQUIRED');
    throw new Error('Failed to load validation summary');
  }
  return res.json();
}

export async function fetchValidationClassification(includeDemo = false, token) {
  const res = await fetch(`${API_BASE}/validation/classification?include_demo=${includeDemo}`, {
    headers: getAdminHeaders(token),
  });
  if (!res.ok) throw new Error('Failed to load classification validation metrics');
  return res.json();
}

export async function fetchValidationRegression(includeDemo = false, token) {
  const res = await fetch(`${API_BASE}/validation/regression?include_demo=${includeDemo}`, {
    headers: getAdminHeaders(token),
  });
  if (!res.ok) throw new Error('Failed to load regression validation metrics');
  return res.json();
}

export async function fetchValidationFeedback(includeDemo = false, token) {
  const res = await fetch(`${API_BASE}/validation/feedback?include_demo=${includeDemo}`, {
    headers: getAdminHeaders(token),
  });
  if (!res.ok) throw new Error('Failed to load feedback analytics');
  return res.json();
}

export async function fetchValidationErrors(includeDemo = false, token) {
  const res = await fetch(`${API_BASE}/validation/errors?include_demo=${includeDemo}`, {
    headers: getAdminHeaders(token),
  });
  if (!res.ok) throw new Error('Failed to load error analysis');
  return res.json();
}

export async function fetchValidationModels(token) {
  const res = await fetch(`${API_BASE}/validation/models`, {
    headers: getAdminHeaders(token),
  });
  if (!res.ok) throw new Error('Failed to load model versions');
  return res.json();
}

export async function adminRetrain(includeDemo = false, force = false, token) {
  const res = await fetch(`${API_BASE}/admin/retrain`, {
    method: 'POST',
    headers: getAdminHeaders(token),
    body: JSON.stringify({ include_demo: includeDemo, force }),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || 'Retraining failed');
  }
  return res.json();
}

export async function adminRollback(targetVersion, token) {
  const res = await fetch(`${API_BASE}/admin/rollback`, {
    method: 'POST',
    headers: getAdminHeaders(token),
    body: JSON.stringify({ target_version: targetVersion }),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || 'Rollback failed');
  }
  return res.json();
}

export async function adminSeedDemo(count = 35, token) {
  const res = await fetch(`${API_BASE}/admin/seed-demo?count=${count}`, {
    method: 'POST',
    headers: getAdminHeaders(token),
  });
  if (!res.ok) throw new Error('Failed to seed demo data');
  return res.json();
}
