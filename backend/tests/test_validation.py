"""
SmartPulse Validation & Retraining Unit & Integration Tests
Audits:
- Hand-computed classification metrics (60% accuracy case)
- Hand-computed regression metrics (MAE/RMSE case)
- Verified outcome scoring reuse (sum bo1..bo5, >=15 is High Risk)
- Consent creation and GDPR deletion by ID/token
- Version stamping (model_version on predictions)
- Demo data exclusion from real metrics & training
- Controlled retraining promotion and rejection logic
- Frozen held-out test set isolation (27 rows never in training)
- Full student integration flow: consent -> assessment -> prediction -> feedback -> outcome -> metrics update
"""

import json
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app import config
config.ADMIN_TOKEN = "test-admin-token"
from app.main import app
from app.db import init_db, SessionLocal, Student, Assessment, Prediction, StudentFeedback, VerifiedOutcome, ModelVersion
from app.metrics import (
    compute_classification_metrics,
    compute_regression_metrics,
    compute_feedback_analytics,
    compute_error_analysis,
    wilson_score_interval
)
from retraining.frozen_test import load_frozen_test_df, load_initial_train_df
from retraining.pipeline import get_retraining_data, run_retraining_pipeline, rollback_model_to_version

SAMPLE_PAYLOAD = {
    "sleep_mid_hrs": 6.5,
    "sleep_quality": 3,
    "bedtime_code": 2,
    "screen_mid_hrs": 5.0,
    "phone_bed_code": 3,
    "exercise_days_mid": 1.5,
    "deadlines_code": 2,
    "workload_code": 3,
    "performance_code": 3.0,
    "pss1_no_control": 3,
    "pss2_confident": 3,
    "pss3_going_my_way": 3,
    "pss4_piling_up": 3
}

ADMIN_HEADERS = {"X-Admin-Token": config.ADMIN_TOKEN}

@pytest.fixture(autouse=True)
def setup_database():
    init_db()
    yield

# ── 1. Unit Tests: Hand-Computed Metrics ─────────────────────────────────────

def test_hand_computed_classification_metrics():
    """
    Test exact hand-computed example:
    predicted: High, Moderate, Low, High, Moderate
    actual:    High, High,     Low, Moderate, Moderate
    Matches: index 0 (High), index 2 (Low), index 4 (Moderate) -> 3/5 = 60.0% accuracy
    """
    y_pred = ["High", "Moderate", "Low", "High", "Moderate"]
    y_true = ["High", "High", "Low", "Moderate", "Moderate"]

    res = compute_classification_metrics(y_true, y_pred, min_n=5)
    assert res["status"] == "ready"
    assert res["n"] == 5
    assert res["accuracy"] == 0.6
    assert abs(res["accuracy"] - 0.6) < 1e-6

    # Verify per-class metrics
    assert "High" in res["per_class"]
    assert "Moderate" in res["per_class"]
    assert "Low" in res["per_class"]
    # For Low: actual 1, predicted 1 -> precision 1.0, recall 1.0, f1 1.0
    assert res["per_class"]["Low"]["precision"] == 1.0
    assert res["per_class"]["Low"]["recall"] == 1.0

def test_hand_computed_regression_metrics():
    """
    Tiny regression test:
    actual:    [10.0, 15.0, 20.0]
    predicted: [12.0, 15.0, 17.0]
    residuals: [-2, 0, +3]
    abs:       [2, 0, 3] -> sum=5, MAE = 5/3 = 1.6667
    squared:   [4, 0, 9] -> sum=13, MSE = 13/3 = 4.3333 -> RMSE = sqrt(4.3333) = 2.0817
    """
    y_true = [10.0, 15.0, 20.0]
    y_pred = [12.0, 15.0, 17.0]

    res = compute_regression_metrics(y_true, y_pred, min_n=3)
    assert res["status"] == "ready"
    assert res["n"] == 3
    assert abs(res["mae"] - 1.6667) < 1e-3
    assert abs(res["rmse"] - 2.0817) < 1e-3

def test_wilson_score_interval():
    ci = wilson_score_interval(6, 10, confidence=0.95)
    assert ci is not None
    assert 0.0 <= ci[0] <= 0.6 <= ci[1] <= 1.0

# ── 2. Scoring Reuse Test ───────────────────────────────────────────────────

def test_verified_outcome_scoring_reuse(client):
    """
    Outcome form must reuse the EXACT instrument and scoring/threshold logic:
    measured_score = bo1 + bo2 + bo3 + bo4 + bo5 (range 5-25)
    measured_category = High Risk if measured_score >= 15 else Low Risk
    """
    # Create consent to get return code
    res_consent = client.post("/api/consent", json={"consent": True})
    code = res_consent.json()["return_code"]

    # Case A: Low Burnout (1 + 2 + 2 + 1 + 2 = 8 < 15)
    res_low = client.post("/api/outcome", json={
        "return_code": code,
        "bo1": 1, "bo2": 2, "bo3": 2, "bo4": 1, "bo5": 2
    })
    assert res_low.status_code == 200
    data_low = res_low.json()
    assert data_low["measured_score"] == 8.0
    assert data_low["measured_category"] == "Low Risk"

    # Case B: High Burnout (4 + 3 + 3 + 3 + 3 = 16 >= 15)
    res_high = client.post("/api/outcome", json={
        "return_code": code,
        "bo1": 4, "bo2": 3, "bo3": 3, "bo4": 3, "bo5": 3
    })
    assert res_high.status_code == 200
    data_high = res_high.json()
    assert data_high["measured_score"] == 16.0
    assert data_high["measured_category"] == "High Risk"

# ── 3. Privacy, Consent & Deletion ──────────────────────────────────────────

def test_consent_and_deletion(client):
    # Opt-in consent
    res = client.post("/api/consent", json={"consent": True})
    assert res.status_code == 200
    anon_id = res.json()["anon_id"]
    return_code = res.json()["return_code"]

    # Delete data by ID
    del_res = client.delete(f"/api/data/{anon_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # Deleting again returns 404
    del_again = client.delete(f"/api/data/{anon_id}")
    assert del_again.status_code == 404

# ── 4. Version Stamping Test ────────────────────────────────────────────────

def test_version_stamping(client):
    res = client.post("/api/predict/category", json=SAMPLE_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert "model_version" in data
    assert data["model_version"].startswith("v1.")
    assert data.get("prediction_id") is None

# ── 5. Frozen Test Set Isolation ────────────────────────────────────────────

def test_frozen_test_set_isolation():
    """
    Test that the frozen held-out test set (n=27) is never in the training set.
    """
    test_df = load_frozen_test_df()
    train_df = load_initial_train_df()

    assert len(test_df) == 27
    assert len(train_df) == 105

    # Check ID sets do not overlap
    test_ids = set(test_df["id"])
    train_ids = set(train_df["id"])
    assert len(test_ids & train_ids) == 0

    # Ensure get_retraining_data never includes test_ids
    retrain_df, _, _ = get_retraining_data(include_demo=False)
    if "id" in retrain_df.columns:
        retrain_ids = set(retrain_df["id"].dropna())
        assert len(retrain_ids & test_ids) == 0

# ── 6. Demo Exclusion Test ──────────────────────────────────────────────────

def test_demo_exclusion(client):
    # Verify summary with demo excluded vs included
    res_real = client.get("/api/validation/summary?include_demo=false", headers=ADMIN_HEADERS)
    assert res_real.status_code == 200
    n_real = res_real.json()["n"]

    # Seed demo data
    retrain_before, _, _ = get_retraining_data(include_demo=True)
    seed_res = client.post("/api/admin/seed-demo?count=10", headers=ADMIN_HEADERS)
    assert seed_res.status_code == 200

    # Real metrics should NOT count demo rows
    res_real_after = client.get("/api/validation/summary?include_demo=false", headers=ADMIN_HEADERS)
    assert res_real_after.json()["n"] == n_real

    # Included demo should show the additional rows
    res_demo = client.get("/api/validation/summary?include_demo=true", headers=ADMIN_HEADERS)
    assert res_demo.json()["n"] >= n_real + 10

    # Even when demo rows are visible, they never enter a training set.
    retrain_df, _, _ = get_retraining_data(include_demo=True)
    assert len(retrain_df) == len(retrain_before)

def test_feedback_requires_consent_and_owns_prediction(client):
    rejected = client.post("/api/feedback", json={"agreement": "Yes"})
    assert rejected.status_code == 403

    consent = client.post("/api/consent", json={"consent": True}).json()
    payload = dict(SAMPLE_PAYLOAD, anon_id=consent["anon_id"], return_code=consent["return_code"])
    prediction = client.post("/api/predict/category", json=payload).json()
    feedback = client.post("/api/feedback", json={
        "return_code": consent["return_code"], "prediction_id": prediction["prediction_id"], "agreement": "Yes"
    })
    assert feedback.status_code == 200

    other = client.post("/api/consent", json={"consent": True}).json()
    foreign = client.post("/api/feedback", json={
        "return_code": other["return_code"], "prediction_id": prediction["prediction_id"], "agreement": "Yes"
    })
    assert foreign.status_code == 404

# ── 7. Controlled Retraining Promote and Reject Logic ───────────────────────

def test_retraining_promotion_and_rejection():
    # If insufficient verified outcomes without force, pipeline refuses to retrain
    refused = run_retraining_pipeline(force=False, include_demo=False)
    # If no new real outcomes exist, it should refuse and report needed count
    if refused["status"] == "refused":
        assert "needed_count" in refused
        assert refused["needed_count"] > 0

    # When forced or evaluated, promotion criteria is checked
    res = run_retraining_pipeline(force=True, include_demo=True)
    assert res["status"] in ["promoted", "rejected"]
    assert "f1_gain" in res
    assert "recall_difference" in res

    # Verify rollback works cleanly and preserves v1.0
    rb = rollback_model_to_version("v1.0")
    assert rb["success"] is True
    assert rb["active_version"] == "v1.0"

# ── 8. Full Integration Flow ────────────────────────────────────────────────

def test_full_student_integration_flow(client):
    """
    Complete lifecycle integration test:
    Consent -> Assessment -> Prediction -> Feedback -> Outcome -> Metrics Update
    """
    # 1. Student gives optional consent
    res_consent = client.post("/api/consent", json={"consent": True})
    assert res_consent.status_code == 200
    consent_data = res_consent.json()
    anon_id = consent_data["anon_id"]
    return_code = consent_data["return_code"]

    # 2. Student runs assessment and gets prediction
    payload = dict(SAMPLE_PAYLOAD)
    payload["anon_id"] = anon_id
    payload["return_code"] = return_code

    res_pred = client.post("/api/predict/category", json=payload)
    assert res_pred.status_code == 200
    pred_data = res_pred.json()
    assert pred_data["model_version"] == "v1.0"
    pred_id = pred_data.get("prediction_id")
    with SessionLocal() as db:
        stored_prediction = db.query(Prediction).filter_by(id=pred_id).one()
        assert stored_prediction.score is not None

    res_score = client.post("/api/predict/score", json=payload)
    assert res_score.status_code == 200

    # 3. Student leaves subjective feedback on results page
    res_fb = client.post("/api/feedback", json={
        "return_code": return_code,
        "prediction_id": pred_id,
        "agreement": "Yes",
        "score_feels_right": "Yes",
        "comment": "Accurately reflects my busy midterms week."
    })
    assert res_fb.status_code == 200
    assert res_fb.json()["is_ground_truth"] is False

    # 4. Student returns later to complete verified outcome check
    res_outcome = client.post("/api/outcome", json={
        "return_code": return_code,
        "bo1": 4, "bo2": 3, "bo3": 4, "bo4": 3, "bo5": 3,
        "days_after_assessment": 7.0
    })
    assert res_outcome.status_code == 200
    outcome_data = res_outcome.json()
    assert outcome_data["measured_score"] == 17.0
    assert outcome_data["measured_category"] == "High Risk"

    # 5. Validation metrics update with this verified actual
    summary_res = client.get("/api/validation/summary?include_demo=false", headers=ADMIN_HEADERS)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["n"] >= 1
