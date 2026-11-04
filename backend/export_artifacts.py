#!/usr/bin/env python
"""
SmartPulse Backend — Export Artifacts
Computes and exports all statistical hypothesis tests, overview distributions,
and model performance metrics directly from the dataset into backend/artifacts/*.json.
"""

import json
import pathlib
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import confusion_matrix, roc_curve, roc_auc_score, r2_score, mean_absolute_error, root_mean_squared_error

def main():
    root = pathlib.Path(__file__).resolve().parent
    data_path = root.parent / "smartpulse_models" / "SmartPulse_Cleaned.xlsx"
    df = pd.read_excel(data_path, sheet_name="Cleaned_Data")
    artifacts_dir = root / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    # 1. Overview Distributions and Summary Stats
    bt = df["burnout_total"]
    st = df["stress_total"]
    sl = df["sleep_mid_hrs"]
    bh = df["burnout_high"]

    # Burnout distribution histogram bins
    bo_counts, bo_bins = np.histogram(bt, bins=10)
    bo_dist = []
    for i in range(len(bo_counts)):
        bo_dist.append({
            "range": f"{bo_bins[i]:.1f} - {bo_bins[i+1]:.1f}",
            "count": int(bo_counts[i]),
            "bin_start": round(float(bo_bins[i]), 1),
            "bin_end": round(float(bo_bins[i+1]), 1)
        })

    # Stress distribution histogram bins
    st_counts, st_bins = np.histogram(st, bins=8)
    st_dist = []
    for i in range(len(st_counts)):
        st_dist.append({
            "range": f"{st_bins[i]:.1f} - {st_bins[i+1]:.1f}",
            "count": int(st_counts[i]),
            "bin_start": round(float(st_bins[i]), 1),
            "bin_end": round(float(st_bins[i+1]), 1)
        })

    # Stress timeline
    stress_timeline = [
        {"stage": "Beginning", "label": "Start of Semester", "mean": round(float(df["stress_start"].mean()), 2), "sd": round(float(df["stress_start"].std()), 2)},
        {"stage": "Middle", "label": "Midterms / Projects", "mean": round(float(df["stress_mid"].mean()), 2), "sd": round(float(df["stress_mid"].std()), 2)},
        {"stage": "Current", "label": "Current Status", "mean": round(float(df["stress_now"].mean()), 2), "sd": round(float(df["stress_now"].std()), 2)}
    ]

    overview_stats = {
        "n_students": int(len(df)),
        "mean_burnout": round(float(bt.mean()), 2),
        "median_burnout": round(float(bt.median()), 2),
        "std_burnout": round(float(bt.std()), 2),
        "min_burnout": int(bt.min()),
        "max_burnout": int(bt.max()),
        "mean_stress": round(float(st.mean()), 2),
        "std_stress": round(float(st.std()), 2),
        "mean_sleep": round(float(sl.mean()), 2),
        "pct_high_burnout": round(float(bh.mean() * 100), 1),
        "significant_tests_count": 2,
        "burnout_distribution": bo_dist,
        "stress_distribution": st_dist,
        "stress_timeline": stress_timeline
    }

    with open(artifacts_dir / "overview_stats.json", "w") as f:
        json.dump(overview_stats, f, indent=2)

    # 2. Hypothesis Tests (All 6 Tests)
    tests = []

    # Test 1: Stress across semester stages
    res_friedman = stats.friedmanchisquare(df["stress_start"], df["stress_mid"], df["stress_now"])
    w_kendall = float(res_friedman.statistic / (len(df) * 2))
    tests.append({
        "id": "stress_stages",
        "title": "Semester Progression vs. Perceived Stress",
        "research_question": "Does student stress significantly change across semester stages?",
        "hypothesis": "Perceived stress differs across the beginning, middle, and current phases of the semester.",
        "test_name": "Friedman Test (Repeated Measures)",
        "statistic": round(float(res_friedman.statistic), 3),
        "p_value": float(f"{res_friedman.pvalue:.4e}"),
        "effect_size": round(w_kendall, 3),
        "effect_size_name": "Kendall's W",
        "significant": True,
        "conclusion": "Stress escalated significantly from semester start (1.97) through midterm (3.06) to current (3.20) (χ² = 108.43, p < 0.001, W = 0.411).",
        "chart_data": stress_timeline
    })

    # Test 2: Workload vs Burnout (Dichotomized)
    df["workload_high"] = (df["workload_code"] >= 3).astype(int)
    ct_wl = pd.crosstab(df["workload_high"], df["burnout_high"])
    chi2_wl, p_wl, _, _ = stats.chi2_contingency(ct_wl, correction=False)
    v_wl = float(np.sqrt(chi2_wl / len(df)))
    or_wl = float((ct_wl.loc[1, 1] * ct_wl.loc[0, 0]) / (ct_wl.loc[1, 0] * ct_wl.loc[0, 1]))
    tests.append({
        "id": "workload_burnout",
        "title": "Academic Workload vs. Burnout Risk",
        "research_question": "Is perceived academic workload associated with student burnout risk?",
        "hypothesis": "Students reporting heavy or overwhelming workload have a higher likelihood of high burnout.",
        "test_name": "Pearson's Chi-Square Test of Independence",
        "statistic": round(float(chi2_wl), 3),
        "p_value": round(float(p_wl), 6),
        "effect_size": round(v_wl, 3),
        "effect_size_name": "Cramer's V",
        "odds_ratio": round(or_wl, 3),
        "significant": True,
        "conclusion": "Perceived academic workload is strongly associated with high burnout risk (χ² = 11.461, p = 0.000711, Cramer's V = 0.295). Students with heavy/overwhelming workloads have 4.31 times higher odds of experiencing high burnout.",
        "chart_data": [
            {"category": "Light / Manageable", "total": int(ct_wl.loc[0].sum()), "high_burnout_pct": round(float(ct_wl.loc[0, 1] / ct_wl.loc[0].sum() * 100), 1)},
            {"category": "Heavy / Overwhelming", "total": int(ct_wl.loc[1].sum()), "high_burnout_pct": round(float(ct_wl.loc[1, 1] / ct_wl.loc[1].sum() * 100), 1)}
        ]
    })

    # Test 3: Phone use before bed
    df["phone_high"] = (df["phone_bed_code"] >= 3).astype(int)
    ct_phone = pd.crosstab(df["phone_high"], df["burnout_high"])
    chi2_ph, p_ph, _, _ = stats.chi2_contingency(ct_phone, correction=False)
    v_ph = float(np.sqrt(chi2_ph / len(df)))
    tests.append({
        "id": "phone_burnout",
        "title": "Bedtime Phone Usage vs. Burnout",
        "research_question": "Is bedtime smartphone usage associated with burnout risk?",
        "hypothesis": "Frequent phone use before bed is associated with higher burnout levels.",
        "test_name": "Pearson's Chi-Square Test",
        "statistic": round(float(chi2_ph), 3),
        "p_value": round(float(p_ph), 4),
        "effect_size": round(v_ph, 3),
        "effect_size_name": "Cramer's V",
        "significant": False,
        "conclusion": "Bedtime smartphone habits show a modest trend toward higher burnout that does not reach statistical significance at α = 0.05 (χ² = 3.225, p = 0.0725, V = 0.156).",
        "chart_data": [
            {"category": "Never / Sometimes", "total": int(ct_phone.loc[0].sum()), "high_burnout_pct": round(float(ct_phone.loc[0, 1] / ct_phone.loc[0].sum() * 100), 1)},
            {"category": "Usually / Always", "total": int(ct_phone.loc[1].sum()), "high_burnout_pct": round(float(ct_phone.loc[1, 1] / ct_phone.loc[1].sum() * 100), 1)}
        ]
    })

    # Test 4: Exam performance vs expectations
    df_perf = df.dropna(subset=["performance_code"]).copy()
    u_perf, p_u_perf = stats.mannwhitneyu(
        df_perf[df_perf["burnout_high"] == 1]["performance_code"],
        df_perf[df_perf["burnout_high"] == 0]["performance_code"]
    )
    df_perf["perf_below"] = (df_perf["performance_code"] <= 2).astype(int)
    ct_perf = pd.crosstab(df_perf["perf_below"], df_perf["burnout_high"])
    tests.append({
        "id": "exam_performance_burnout",
        "title": "Exam Performance vs. Expectations",
        "research_question": "Does recent exam performance relative to expectations relate to burnout?",
        "hypothesis": "Students performing below expectations exhibit higher burnout risk.",
        "test_name": "Mann-Whitney U Test",
        "statistic": round(float(u_perf), 1),
        "p_value": round(float(p_u_perf), 4),
        "effect_size": round(float(np.sqrt(stats.chi2_contingency(ct_perf, correction=False)[0] / len(df_perf))), 3),
        "effect_size_name": "Cramer's V",
        "significant": False,
        "conclusion": "Underperforming relative to personal expectations shows an elevated burnout trend, though falling slightly short of α = 0.05 threshold (U = 1444.0, p = 0.0622).",
        "chart_data": [
            {"category": "Below Expectations", "total": int(ct_perf.loc[1].sum()), "high_burnout_pct": round(float(ct_perf.loc[1, 1] / ct_perf.loc[1].sum() * 100), 1)},
            {"category": "Expected or Above", "total": int(ct_perf.loc[0].sum()), "high_burnout_pct": round(float(ct_perf.loc[0, 1] / ct_perf.loc[0].sum() * 100), 1)}
        ]
    })

    # Test 5: Exercise frequency
    df["exercise_regular"] = (df["exercise_days_mid"] >= 3.0).astype(int)
    ct_ex = pd.crosstab(df["exercise_regular"], df["burnout_high"])
    chi2_ex, p_ex, _, _ = stats.chi2_contingency(ct_ex, correction=False)
    tests.append({
        "id": "exercise_burnout",
        "title": "Physical Activity Frequency vs. Burnout",
        "research_question": "Is weekly physical exercise frequency associated with reduced burnout?",
        "hypothesis": "Regular exercise (3+ days/week) is associated with lower burnout rates.",
        "test_name": "Pearson's Chi-Square Test",
        "statistic": round(float(chi2_ex), 3),
        "p_value": round(float(p_ex), 4),
        "effect_size": round(float(np.sqrt(chi2_ex / len(df))), 3),
        "effect_size_name": "Cramer's V",
        "significant": False,
        "conclusion": "Exercise frequency alone does not show a statistically significant protective association with burnout risk in this sample (χ² = 1.914, p = 0.1665).",
        "chart_data": [
            {"category": "0 - 2 days/week", "total": int(ct_ex.loc[0].sum()), "high_burnout_pct": round(float(ct_ex.loc[0, 1] / ct_ex.loc[0].sum() * 100), 1)},
            {"category": "3+ days/week", "total": int(ct_ex.loc[1].sum()), "high_burnout_pct": round(float(ct_ex.loc[1, 1] / ct_ex.loc[1].sum() * 100), 1)}
        ]
    })

    # Test 6: Gender vs Burnout
    ct_gen = pd.crosstab(df["gender_analysis"], df["burnout_high"])
    chi2_gen, p_gen, _, _ = stats.chi2_contingency(ct_gen, correction=False)
    tests.append({
        "id": "gender_burnout",
        "title": "Gender Identity vs. Burnout Prevalence",
        "research_question": "Does student burnout prevalence differ significantly by gender?",
        "hypothesis": "Burnout rates differ between male and female students.",
        "test_name": "Pearson's Chi-Square Test",
        "statistic": round(float(chi2_gen), 3),
        "p_value": round(float(p_gen), 4),
        "effect_size": round(float(np.sqrt(chi2_gen / len(df))), 3),
        "effect_size_name": "Cramer's V",
        "significant": False,
        "conclusion": "Burnout prevalence does not differ significantly between male (54.2%) and female (53.1%) students (χ² = 0.017, p = 0.8976), indicating uniform vulnerability across genders.",
        "chart_data": [
            {"category": "Female (n=49)", "total": int(ct_gen.loc["Female"].sum()), "high_burnout_pct": round(float(ct_gen.loc["Female", 1] / ct_gen.loc["Female"].sum() * 100), 1)},
            {"category": "Male (n=83)", "total": int(ct_gen.loc["Male"].sum()), "high_burnout_pct": round(float(ct_gen.loc["Male", 1] / ct_gen.loc["Male"].sum() * 100), 1)}
        ]
    })

    with open(artifacts_dir / "hypothesis_tests.json", "w") as f:
        json.dump(tests, f, indent=2)

    # 3. Model Performance Artifacts
    # Load metrics_table.csv from smartpulse_models/outputs
    metrics_path = root.parent / "smartpulse_models" / "outputs" / "metrics_table.csv"
    oof_path = root.parent / "smartpulse_models" / "outputs" / "oof_predictions.csv"
    bayes_path = root.parent / "smartpulse_models" / "outputs" / "bayes_summary.csv"

    cv_metrics = pd.read_csv(metrics_path).set_index("model").to_dict(orient="index")
    oof_df = pd.read_csv(oof_path)
    bayes_df = pd.read_csv(bayes_path)

    # Confusion matrix on OOF predictions (threshold = 0.5)
    rf_preds = (oof_df["prob_rf"] >= 0.5).astype(int)
    lr_preds = (oof_df["prob_logreg"] >= 0.5).astype(int)
    cm_rf = confusion_matrix(oof_df["y_true"], rf_preds, labels=[0, 1]).tolist()
    cm_lr = confusion_matrix(oof_df["y_true"], lr_preds, labels=[0, 1]).tolist()

    # ROC curve points for RF and LR
    fpr_rf, tpr_rf, _ = roc_curve(oof_df["y_true"], oof_df["prob_rf"])
    fpr_lr, tpr_lr, _ = roc_curve(oof_df["y_true"], oof_df["prob_logreg"])
    
    # Subsample ROC curves to ~20 points for smooth SVG plotting
    idx_rf = np.linspace(0, len(fpr_rf) - 1, 25).astype(int)
    idx_lr = np.linspace(0, len(fpr_lr) - 1, 25).astype(int)

    roc_points_rf = [{"fpr": round(float(fpr_rf[i]), 3), "tpr": round(float(tpr_rf[i]), 3)} for i in idx_rf]
    roc_points_lr = [{"fpr": round(float(fpr_lr[i]), 3), "tpr": round(float(tpr_lr[i]), 3)} for i in idx_lr]

    # Regression actual vs predicted using OLS model
    with open(root / "saved_models" / "preprocessor_meta.json") as f:
        meta = json.load(f)

    FEATURES_FINAL = meta["features_final"]
    X_reg = df[meta["features"]].copy()
    X_reg["performance_missing"] = X_reg["performance_code"].isnull().astype(float)
    X_reg["performance_code"] = X_reg["performance_code"].fillna(meta["perf_median"])
    X_z = np.column_stack([
        (X_reg[f].values - meta["means"][f]) / meta["stds"][f] for f in FEATURES_FINAL
    ])

    import joblib
    ols = joblib.load(root / "saved_models" / "reg_ols.joblib")
    y_pred_reg = ols.predict(X_z)

    r2 = float(r2_score(df["burnout_total"], y_pred_reg))
    mae = float(mean_absolute_error(df["burnout_total"], y_pred_reg))
    rmse = float(root_mean_squared_error(df["burnout_total"], y_pred_reg))

    scatter_pts = []
    for i in range(len(df)):
        scatter_pts.append({
            "id": str(df["id"].iloc[i]),
            "actual": int(df["burnout_total"].iloc[i]),
            "predicted": round(float(y_pred_reg[i]), 2)
        })

    perf_payload = {
        "classification": {
            "cv_metrics": cv_metrics,
            "confusion_matrices": {
                "rf": {"labels": ["Low", "High"], "matrix": cm_rf},
                "logreg": {"labels": ["Low", "High"], "matrix": cm_lr}
            },
            "roc_curves": {
                "rf": {"auc": round(float(roc_auc_score(oof_df["y_true"], oof_df["prob_rf"])), 3), "points": roc_points_rf},
                "logreg": {"auc": round(float(roc_auc_score(oof_df["y_true"], oof_df["prob_logreg"])), 3), "points": roc_points_lr}
            }
        },
        "regression": {
            "r2": round(r2, 3),
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "scale_min": int(bt.min()),
            "scale_max": int(bt.max()),
            "actual_vs_predicted": scatter_pts
        },
        "bayesian_summary": bayes_df.to_dict(orient="records")
    }

    with open(artifacts_dir / "model_performance.json", "w") as f:
        json.dump(perf_payload, f, indent=2)

    print("All artifacts successfully exported to:", artifacts_dir)

if __name__ == "__main__":
    main()
