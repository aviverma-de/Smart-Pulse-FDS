#!/usr/bin/env python
"""
SmartPulse Backend — Model Training and Persistence
Trains the exact models from 01_classifier.py and 02_bayesian_regression.py
and saves serialized joblib pipelines and metadata.
"""

import os
import json
import pathlib
import numpy as np
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier

SEED = 42

def find_dataset():
    current_dir = pathlib.Path(__file__).resolve().parent
    candidates = [
        current_dir.parent / "smartpulse_models" / "SmartPulse_Cleaned.xlsx",
        current_dir.parent / "CleanedData" / "SmartPulse_Cleaned (1).xlsx",
        pathlib.Path("smartpulse_models/SmartPulse_Cleaned.xlsx"),
    ]
    for c in candidates:
        if c.exists():
            return c.resolve()
    raise FileNotFoundError("SmartPulse_Cleaned.xlsx not found.")

def main():
    np.random.seed(SEED)
    current_dir = pathlib.Path(__file__).resolve().parent
    data_path = find_dataset()
    df = pd.read_excel(data_path, sheet_name="Cleaned_Data")
    print(f"Loaded {len(df)} rows from {data_path}")

    save_dir = pathlib.Path(__file__).resolve().parent / "saved_models"
    save_dir.mkdir(exist_ok=True)
    artifacts_dir = pathlib.Path(__file__).resolve().parent / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    FEATURES = [
        "sleep_mid_hrs", "sleep_quality", "bedtime_code",
        "screen_mid_hrs", "phone_bed_code",
        "exercise_days_mid", "deadlines_code",
        "workload_code", "performance_code",
    ]
    
    # 1. Prepare Features
    X = df[FEATURES].copy()
    X["performance_missing"] = X["performance_code"].isnull().astype(float)
    FEATURES_FINAL = FEATURES + ["performance_missing"]

    y_class = df["burnout_high"].copy()
    y_reg = df["burnout_total"].copy().values.astype(float)

    # 2. Classifier Pipeline Setup (exact from 01_classifier.py)
    numeric_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    preprocessor = ColumnTransformer(
        transformers=[("num", numeric_transformer, FEATURES_FINAL)],
        remainder="drop",
    )

    pipe_lr = Pipeline([
        ("pre", preprocessor),
        ("clf", LogisticRegression(
            penalty="l2", C=1.0, solver="lbfgs", max_iter=1000, random_state=SEED
        )),
    ])

    pipe_rf = Pipeline([
        ("pre", preprocessor),
        ("clf", RandomForestClassifier(
            n_estimators=500, max_depth=4, min_samples_leaf=5,
            random_state=SEED, n_jobs=1
        )),
    ])

    print("Fitting Logistic Regression and Random Forest...")
    pipe_lr.fit(X[FEATURES_FINAL], y_class)
    pipe_rf.fit(X[FEATURES_FINAL], y_class)

    # 3. Regression Setup (OLS and Bayesian metadata)
    perf_median = float(df["performance_code"].median())
    X_reg = X.copy()
    X_reg["performance_code"] = X_reg["performance_code"].fillna(perf_median)
    
    X_means = X_reg[FEATURES_FINAL].mean().to_dict()
    X_stds = X_reg[FEATURES_FINAL].std(ddof=0).to_dict()
    for k, v in X_stds.items():
        if v < 1e-8:
            X_stds[k] = 1.0

    # Z-score standardization for regression
    X_z = np.column_stack([
        (X_reg[f].values - X_means[f]) / X_stds[f] for f in FEATURES_FINAL
    ])

    ols = LinearRegression()
    ols.fit(X_z, y_reg)

    # Load Bayesian summary from outputs/bayes_summary.csv if available
    bayes_summary_path = current_dir.parent / "smartpulse_models" / "outputs" / "bayes_summary.csv"
    if bayes_summary_path.exists():
        bayes_df = pd.read_csv(bayes_summary_path)
        bayes_params = bayes_df.to_dict(orient="records")
    else:
        bayes_params = []

    # Save artifacts
    joblib.dump(pipe_lr, save_dir / "pipe_lr.joblib")
    joblib.dump(pipe_rf, save_dir / "pipe_rf.joblib")
    joblib.dump(ols, save_dir / "reg_ols.joblib")

    meta = {
        "features": FEATURES,
        "features_final": FEATURES_FINAL,
        "perf_median": perf_median,
        "means": X_means,
        "stds": X_stds,
        "ols_intercept": float(ols.intercept_),
        "ols_coefs": {f: float(c) for f, c in zip(FEATURES_FINAL, ols.coef_)},
        "n_samples": len(df),
        "target_class": "burnout_high",
        "target_reg": "burnout_total",
        "burnout_min": int(y_reg.min()),
        "burnout_max": int(y_reg.max()),
        "burnout_mean": float(y_reg.mean()),
        "burnout_std": float(y_reg.std()),
        "burnout_median": float(np.median(y_reg))
    }

    with open(save_dir / "preprocessor_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    with open(save_dir / "bayes_params.json", "w") as f:
        json.dump(bayes_params, f, indent=2)

    print("Successfully saved models and metadata to:", save_dir)

    # Verification run on 10 rows
    print("\n--- Model Verification on 5 Sample Rows ---")
    sample_X = X[FEATURES_FINAL].head(5)
    probs_rf = pipe_rf.predict_proba(sample_X)[:, 1]
    probs_lr = pipe_lr.predict_proba(sample_X)[:, 1]
    
    # Regression prediction
    sample_reg = sample_X.copy()
    sample_reg["performance_code"] = sample_reg["performance_code"].fillna(perf_median)
    sample_z = np.column_stack([
        (sample_reg[f].values - X_means[f]) / X_stds[f] for f in FEATURES_FINAL
    ])
    preds_ols = ols.predict(sample_z)

    for i in range(5):
        print(f"Row {i}: True Y_class={y_class.iloc[i]}, RF_Prob={probs_rf[i]:.4f}, LR_Prob={probs_lr[i]:.4f}, True Y_reg={y_reg[i]:.1f}, OLS_Pred={preds_ols[i]:.2f}")

if __name__ == "__main__":
    main()
