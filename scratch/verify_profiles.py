import urllib.request
import json
import joblib
import pandas as pd
import numpy as np

# Load models directly
pipe_rf = joblib.load('backend/saved_models/pipe_rf.joblib')
pipe_lr = joblib.load('backend/saved_models/pipe_lr.joblib')
with open('backend/saved_models/preprocessor_meta.json') as f:
    meta = json.load(f)
with open('backend/saved_models/bayes_params.json') as f:
    bayes_params = json.load(f)

bayes_dict = {p['feature']: p['posterior_mean'] for p in bayes_params}

def direct_predict(inp):
    row = {
        "sleep_mid_hrs": float(inp["sleep_mid_hrs"]),
        "sleep_quality": int(inp["sleep_quality"]),
        "bedtime_code": int(inp["bedtime_code"]),
        "screen_mid_hrs": float(inp["screen_mid_hrs"]),
        "phone_bed_code": int(inp["phone_bed_code"]),
        "exercise_days_mid": float(inp["exercise_days_mid"]),
        "deadlines_code": int(inp["deadlines_code"]),
        "workload_code": int(inp["workload_code"]),
        "performance_code": float(inp["performance_code"]) if inp["performance_code"] is not None else np.nan,
        "performance_missing": 1.0 if inp["performance_code"] is None else 0.0,
    }
    df = pd.DataFrame([row])
    
    # RF Prob
    rf_prob = pipe_rf.predict_proba(df)[0]
    rf_cat = "High Risk" if rf_prob[1] >= 0.5 else "Low Risk"
    
    # Score
    df_reg = df.copy()
    df_reg["performance_code"] = df_reg["performance_code"].fillna(meta["perf_median"])
    z_vals = [
        (df_reg[col].iloc[0] - meta["means"][col]) / meta["stds"][col] for col in meta["features_final"]
    ]
    score = bayes_dict.get("intercept", meta["ols_intercept"])
    for col, z in zip(meta["features_final"], z_vals):
        score += bayes_dict.get(col, meta["ols_coefs"].get(col, 0.0)) * z
        
    return {
        "rf_prob_high": round(float(rf_prob[1]), 4),
        "rf_cat": rf_cat,
        "bayes_score": round(float(score), 2)
    }

def api_call(endpoint, payload):
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/{endpoint}",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

profiles = [
    {
        "name": "Profile 1 (High Stress / Exhausted)",
        "input": {
            "sleep_mid_hrs": 4.5, "sleep_quality": 1, "bedtime_code": 4,
            "screen_mid_hrs": 9.0, "phone_bed_code": 4, "exercise_days_mid": 0.0,
            "deadlines_code": 4, "workload_code": 4, "performance_code": 1.0
        }
    },
    {
        "name": "Profile 2 (Balanced / Low Risk)",
        "input": {
            "sleep_mid_hrs": 8.5, "sleep_quality": 5, "bedtime_code": 1,
            "screen_mid_hrs": 3.0, "phone_bed_code": 1, "exercise_days_mid": 5.5,
            "deadlines_code": 1, "workload_code": 1, "performance_code": 5.0
        }
    },
    {
        "name": "Profile 3 (Average Student / No Exam History)",
        "input": {
            "sleep_mid_hrs": 6.5, "sleep_quality": 3, "bedtime_code": 2,
            "screen_mid_hrs": 5.0, "phone_bed_code": 3, "exercise_days_mid": 1.5,
            "deadlines_code": 2, "workload_code": 2, "performance_code": None
        }
    }
]

print("=== VERIFYING THREE PROFILES ACROSS DIRECT PYTHON AND HTTP API ===")
for p in profiles:
    print(f"\n--- {p['name']} ---")
    direct = direct_predict(p["input"])
    api_cat = api_call("predict/category", p["input"])
    api_score = api_call("predict/score", p["input"])
    
    print(f"Direct Model : Cat={direct['rf_cat']}, Prob_High={direct['rf_prob_high']}, Score={direct['bayes_score']}")
    print(f"API Endpoint : Cat={api_cat['category']}, Prob_High={api_cat['probabilities']['high']}, Score={api_score['predicted_score']}")
    
    # Assert exact match
    assert direct['rf_cat'] == api_cat['category'], "Category mismatch!"
    assert direct['rf_prob_high'] == api_cat['probabilities']['high'], "Probability mismatch!"
    assert direct['bayes_score'] == api_score['predicted_score'], "Score mismatch!"
    print(">>> EXACT MATCH CONFIRMED!")

print("\nAll 3 profiles verified successfully!")
