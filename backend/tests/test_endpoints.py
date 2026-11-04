import pytest
from app import config

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

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_overview_endpoint(client):
    res = client.get("/api/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["n_students"] == 132
    assert data["mean_burnout"] == 14.98
    assert data["mean_stress"] == 11.66
    assert data["mean_sleep"] == 6.55
    assert "burnout_distribution" in data
    assert "stress_timeline" in data
    assert len(data["stress_timeline"]) == 3

def test_predict_category_endpoint(client):
    res = client.post("/api/predict/category", json=SAMPLE_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert data["category"] in ["High Risk", "Low Risk"]
    assert "probabilities" in data
    assert "high" in data["probabilities"]
    assert "low" in data["probabilities"]
    assert 0.0 <= data["probabilities"]["high"] <= 1.0
    assert "disclaimer" in data
    assert len(data["disclaimer"]) > 20

def test_predict_score_endpoint(client):
    res = client.post("/api/predict/score", json=SAMPLE_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert 5.0 <= data["predicted_score"] <= 25.0
    assert data["scale_min"] == 5
    assert data["scale_max"] == 25
    assert 0.0 <= data["percentile"] <= 100.0
    assert "credible_interval_94" in data
    assert "disclaimer" in data

def test_whatif_endpoint(client):
    modified = dict(SAMPLE_PAYLOAD)
    modified["workload_code"] = 1  # Reduce workload
    modified["phone_bed_code"] = 1 # Stop using phone in bed

    res = client.post("/api/whatif", json={"baseline": SAMPLE_PAYLOAD, "modified": modified})
    assert res.status_code == 200
    data = res.json()
    assert "baseline" in data
    assert "modified" in data
    assert "score_difference" in data
    assert data["score_difference"] < 0  # Score should improve (decrease)
    assert data["direction"] == "improved"
    assert "caution" in data
    assert "disclaimer" in data

def test_explain_endpoint(client):
    res = client.post("/api/explain", json=SAMPLE_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert "method" in data
    assert "contributions" in data
    assert len(data["contributions"]) == 10
    assert "top_factors" in data
    assert len(data["top_factors"]) >= 3
    assert "disclaimer" in data

def test_stats_insights_endpoint(client):
    res = client.get("/api/stats/insights")
    assert res.status_code == 200
    data = res.json()
    assert "tests" in data
    assert len(data["tests"]) == 6
    # Check Workload test matches verified facts
    wl_test = next(t for t in data["tests"] if t["id"] == "workload_burnout")
    assert wl_test["statistic"] == 11.461
    assert wl_test["p_value"] == 0.000711
    assert wl_test["effect_size"] == 0.295
    assert wl_test["odds_ratio"] == 4.314
    assert wl_test["significant"] is True

def test_model_performance_endpoint(client):
    res = client.get("/api/model/performance")
    assert res.status_code == 200
    data = res.json()
    assert "classification" in data
    assert "regression" in data
    assert "bayesian_summary" in data
    assert "actual_vs_predicted" in data["regression"]
    assert len(data["regression"]["actual_vs_predicted"]) == 132

def test_report_pdf_endpoint(client):
    # First get predictions
    cat_res = client.post("/api/predict/category", json=SAMPLE_PAYLOAD).json()
    score_res = client.post("/api/predict/score", json=SAMPLE_PAYLOAD).json()
    exp_res = client.post("/api/explain", json=SAMPLE_PAYLOAD).json()

    report_payload = {
        "inputs": SAMPLE_PAYLOAD,
        "prediction": cat_res,
        "score": score_res,
        "explanation": exp_res,
        "student_name": "Test Student",
        "opt_in_storage": False
    }

    res = client.post("/api/report", json=report_payload)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 1000 # Valid non-empty PDF
    assert res.content[:4] == b"%PDF"
