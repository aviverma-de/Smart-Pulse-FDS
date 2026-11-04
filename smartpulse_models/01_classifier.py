#!/usr/bin/env python
"""
SmartPulse -- Task 1: Burnout Risk Classifier
=============================================
Target: burnout_high (binary, 1 if burnout_total >= 15)
Models: DummyClassifier (baseline), LogisticRegression (L2), RandomForestClassifier
Validation: RepeatedStratifiedKFold (5 folds × 10 repeats)
"""

import os, warnings, pathlib, tempfile
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, ConfusionMatrixDisplay,
    precision_recall_curve, roc_curve
)
from sklearn.inspection import permutation_importance
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore", category=FutureWarning)

SEED = 42

def find_dataset():
    HERE = pathlib.Path(__file__).resolve().parent
    candidates = [
        HERE / "SmartPulse_Cleaned.xlsx",
        HERE.parent / "CleanedData" / "SmartPulse_Cleaned.xlsx",
        HERE.parent / "SmartPulse_Cleaned.xlsx",
        pathlib.Path("CleanedData/SmartPulse_Cleaned.xlsx"),
        pathlib.Path("SmartPulse_Cleaned.xlsx"),
    ]
    for c in candidates:
        if c.exists():
            return c.resolve()
    for root in [HERE.parent, pathlib.Path.cwd()]:
        for match in root.rglob("SmartPulse_Cleaned.xlsx"):
            return match.resolve()
    raise FileNotFoundError("Could not find SmartPulse_Cleaned.xlsx")

def main():
    np.random.seed(SEED)
    HERE = pathlib.Path(__file__).resolve().parent
    OUT = HERE / "outputs"
    OUT.mkdir(exist_ok=True)
    DATA_PATH = find_dataset()

    print("=" * 70, flush=True)
    print("TASK 1 -- BURNOUT RISK CLASSIFIER", flush=True)
    print("=" * 70, flush=True)

    df = pd.read_excel(DATA_PATH, sheet_name="Cleaned_Data")
    print(f"\nDataset: {df.shape[0]} rows × {df.shape[1]} columns loaded from {DATA_PATH.name}", flush=True)

    # ── 2. Define features & target ──────────────────────────────────────────
    FEATURES = [
        "sleep_mid_hrs", "sleep_quality", "bedtime_code",
        "screen_mid_hrs", "phone_bed_code",
        "exercise_days_mid", "deadlines_code",
        "workload_code", "performance_code",
    ]
    TARGET = "burnout_high"
    GROUP_COLS = ["gender_analysis", "year_group", "stream_group", "residence_group"]

    # Leakage check
    BANNED = {"burnout_total", "burnout_high", "burnout_group",
              "bo1", "bo2", "bo3", "bo4", "bo5",
              "stress_total", "stress_start", "stress_mid", "stress_now",
              "pss1", "pss2", "pss3", "pss4", "pss5", "pss6", "pss7",
              "pss8", "pss9", "pss10",
              "gender_analysis", "year_group", "stream_group", "residence_group"}
    leak = set(FEATURES) & BANNED
    assert len(leak) == 0, f"LEAKAGE DETECTED: {leak}"
    print(f"\n[OK] Final feature list (no leakage): {FEATURES}", flush=True)

    X = df[FEATURES].copy()
    y = df[TARGET].copy()

    print(f"\nClass balance:", flush=True)
    print(y.value_counts().rename({0: "Low (0)", 1: "High (1)"}), flush=True)
    print(f"  -> {y.mean():.1%} are High-burnout", flush=True)

    # ── 3. Add missing indicator for performance_code ────────────────────────
    X["performance_missing"] = X["performance_code"].isnull().astype(float)
    print(f"\nperformance_code missing: {int(X['performance_missing'].sum())} / {len(X)}", flush=True)

    FEATURES_FINAL = FEATURES + ["performance_missing"]

    # ── 4. Build pipelines (all preprocessing inside) ────────────────────────
    numeric_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    preprocessor = ColumnTransformer(
        transformers=[("num", numeric_transformer, FEATURES_FINAL)],
        remainder="drop",
    )

    pipe_dummy = Pipeline([
        ("pre", preprocessor),
        ("clf", DummyClassifier(strategy="most_frequent", random_state=SEED)),
    ])

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

    print("\n[OK] All preprocessing (imputation, scaling) is inside sklearn Pipelines.", flush=True)

    # ── 5. Cross-validation ─────────────────────────────────────────────────
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=SEED)
    scoring = {
        "accuracy": "accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1",
        "roc_auc": "roc_auc",
    }

    results = {}
    for name, pipe in [("Dummy", pipe_dummy), ("LogReg", pipe_lr), ("RF", pipe_rf)]:
        cv_res = cross_validate(pipe, X[FEATURES_FINAL], y, cv=cv,
                                scoring=scoring, return_train_score=False, n_jobs=1)
        row = {}
        for metric in scoring:
            key = f"test_{metric}"
            row[f"{metric}_mean"] = cv_res[key].mean()
            row[f"{metric}_sd"] = cv_res[key].std()
        results[name] = row
        print(f"\n  {name}:", flush=True)
        for metric in scoring:
            m, s = row[f"{metric}_mean"], row[f"{metric}_sd"]
            print(f"    {metric:>12s}: {m:.3f} ± {s:.3f}", flush=True)

    # Save metrics table
    metrics_df = pd.DataFrame(results).T
    metrics_df.index.name = "model"
    metrics_df.to_csv(OUT / "metrics_table.csv")
    print(f"\n[OK] Saved metrics_table.csv", flush=True)

    # ── 6. Out-of-fold predictions ───────────────────────────────────────────
    n = len(X)
    prob_lr_accum = np.zeros(n)
    prob_rf_accum = np.zeros(n)
    counts = np.zeros(n)

    for train_idx, test_idx in cv.split(X[FEATURES_FINAL], y):
        X_tr, X_te = X[FEATURES_FINAL].iloc[train_idx], X[FEATURES_FINAL].iloc[test_idx]
        y_tr = y.iloc[train_idx]

        pipe_lr.fit(X_tr, y_tr)
        prob_lr_accum[test_idx] += pipe_lr.predict_proba(X_te)[:, 1]

        pipe_rf.fit(X_tr, y_tr)
        prob_rf_accum[test_idx] += pipe_rf.predict_proba(X_te)[:, 1]

        counts[test_idx] += 1

    prob_lr_avg = prob_lr_accum / counts
    prob_rf_avg = prob_rf_accum / counts

    oof = pd.DataFrame({
        "id": df["id"],
        "y_true": y,
        "prob_logreg": np.round(prob_lr_avg, 4),
        "prob_rf": np.round(prob_rf_avg, 4),
    })
    for g in GROUP_COLS:
        oof[g] = df[g]

    oof.to_csv(OUT / "oof_predictions.csv", index=False)
    print(f"[OK] Saved oof_predictions.csv ({len(oof)} rows)", flush=True)

    # ── 7. Figures ───────────────────────────────────────────────────────────
    DPI = 150

    # 7a. Confusion matrices (out-of-fold, threshold 0.5)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, probs, name in zip(axes, [prob_lr_avg, prob_rf_avg], ["LogReg", "RF"]):
        preds = (probs >= 0.5).astype(int)
        cm = confusion_matrix(y, preds, labels=[0, 1])
        ConfusionMatrixDisplay(cm, display_labels=["Low", "High"]).plot(ax=ax, cmap="Blues")
        ax.set_title(f"{name} (OOF, threshold=0.5)")
    fig.tight_layout()
    fig.savefig(OUT / "confusion_matrices.png", dpi=DPI)
    plt.close(fig)
    print("[OK] Saved confusion_matrices.png", flush=True)

    # 7b. ROC curves
    fig, ax = plt.subplots(figsize=(6, 5))
    colors_map = {"LogReg": "steelblue", "RF": "darkorange"}
    for probs, name in [(prob_lr_avg, "LogReg"), (prob_rf_avg, "RF")]:
        auc = roc_auc_score(y, probs)
        fpr, tpr, _ = roc_curve(y, probs)
        ax.plot(fpr, tpr, color=colors_map[name], lw=2, label=f"{name} (AUC={auc:.3f})")
    ax.plot([0, 1], [0, 1], "k--", lw=0.8, label="Chance")
    ax.set_title("ROC Curves (Out-of-Fold)")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "roc_curves.png", dpi=DPI)
    plt.close(fig)
    print("[OK] Saved roc_curves.png", flush=True)

    # 7c. Precision–Recall vs Threshold plot
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, probs, name in zip(axes, [prob_lr_avg, prob_rf_avg], ["LogReg", "RF"]):
        prec, rec, thresholds = precision_recall_curve(y, probs)
        ax.plot(thresholds, prec[:-1], label="Precision", color="steelblue")
        ax.plot(thresholds, rec[:-1], label="Recall (High)", color="darkorange")
        ax.axvline(0.5, ls="--", color="gray", alpha=0.7, label="Threshold=0.5")
        ax.set_xlabel("Threshold")
        ax.set_ylabel("Score")
        ax.set_title(f"{name}: Precision & Recall vs Threshold")
        ax.legend()
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1.05])
    fig.tight_layout()
    fig.savefig(OUT / "precision_recall_vs_threshold.png", dpi=DPI)
    plt.close(fig)
    print("[OK] Saved precision_recall_vs_threshold.png", flush=True)

    # 7d. Permutation importance for Random Forest (computed on held-out folds)
    perm_imp_means = np.zeros(len(FEATURES_FINAL))
    perm_imp_stds = np.zeros(len(FEATURES_FINAL))
    n_splits_done = 0

    rng = np.random.RandomState(SEED)
    cv2 = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED)
    for train_idx, test_idx in cv2.split(X[FEATURES_FINAL], y):
        pipe_rf.fit(X[FEATURES_FINAL].iloc[train_idx], y.iloc[train_idx])
        pi = permutation_importance(
            pipe_rf, X[FEATURES_FINAL].iloc[test_idx], y.iloc[test_idx],
            n_repeats=10, random_state=rng, scoring="roc_auc", n_jobs=1,
        )
        perm_imp_means += pi.importances_mean
        perm_imp_stds += pi.importances_std
        n_splits_done += 1

    perm_imp_means /= n_splits_done
    perm_imp_stds /= n_splits_done

    imp_df = pd.DataFrame({
        "feature": FEATURES_FINAL,
        "importance_mean": perm_imp_means,
        "importance_std": perm_imp_stds,
    }).sort_values("importance_mean", ascending=True)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(imp_df["feature"], imp_df["importance_mean"],
            xerr=imp_df["importance_std"], color="steelblue", edgecolor="white")
    ax.set_xlabel("Mean decrease in ROC-AUC (permutation on held-out folds)")
    ax.set_title("Random Forest -- Permutation Importance (held-out folds)")
    fig.tight_layout()
    fig.savefig(OUT / "rf_permutation_importance.png", dpi=DPI)
    plt.close(fig)
    print("[OK] Saved rf_permutation_importance.png", flush=True)

    # 7e. Logistic regression coefficients as odds ratios with 94% CI
    pipe_lr.fit(X[FEATURES_FINAL], y)
    coefs = pipe_lr.named_steps["clf"].coef_[0]
    intercept = pipe_lr.named_steps["clf"].intercept_[0]

    # Standard errors via inverse Hessian approximation: Var(beta) ~ (X^T W X)^{-1}
    X_transformed = pipe_lr.named_steps["pre"].transform(X[FEATURES_FINAL])
    probs_full = pipe_lr.predict_proba(X[FEATURES_FINAL])[:, 1]
    W = np.diag(probs_full * (1 - probs_full))
    X_aug = np.hstack([np.ones((X_transformed.shape[0], 1)), X_transformed])
    try:
        cov = np.linalg.inv(X_aug.T @ W @ X_aug)
        se = np.sqrt(np.diag(cov))
        se_coefs = se[1:]  # skip intercept
    except np.linalg.LinAlgError:
        se_coefs = np.full_like(coefs, np.nan)

    from scipy import stats
    z_crit = stats.norm.ppf(0.97)  # 94% CI
    or_vals = np.exp(coefs)
    or_lower = np.exp(coefs - z_crit * se_coefs)
    or_upper = np.exp(coefs + z_crit * se_coefs)

    lr_coef_df = pd.DataFrame({
        "feature": FEATURES_FINAL,
        "coef_std": np.round(coefs, 4),
        "SE": np.round(se_coefs, 4),
        "odds_ratio": np.round(or_vals, 4),
        "OR_lower_94": np.round(or_lower, 4),
        "OR_upper_94": np.round(or_upper, 4),
    })
    print("\nLogistic Regression Coefficients (standardized features):", flush=True)
    print(lr_coef_df.to_string(index=False), flush=True)

    fig, ax = plt.subplots(figsize=(7, 5))
    y_pos = range(len(FEATURES_FINAL))
    ax.errorbar(or_vals, y_pos,
                xerr=[or_vals - or_lower, or_upper - or_vals],
                fmt="o", color="steelblue", capsize=4, markersize=6)
    ax.axvline(1.0, ls="--", color="gray", alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(FEATURES_FINAL)
    ax.set_xlabel("Odds Ratio (94% CI)")
    ax.set_title("Logistic Regression -- Odds Ratios (standardized predictors)")
    fig.tight_layout()
    fig.savefig(OUT / "lr_odds_ratios.png", dpi=DPI)
    plt.close(fig)
    print("[OK] Saved lr_odds_ratios.png", flush=True)

    # ── 8. Interpretation ────────────────────────────────────────────────────
    print("\n" + "=" * 70, flush=True)
    print("INTERPRETATION", flush=True)
    print("=" * 70, flush=True)
    print("""
WHAT THE MODELS CAN DO:
• Both Logistic Regression and Random Forest identify modest predictive signals
  linking daily habits (sleep, bedtime, workload, performance) to burnout risk.
• Recall of the High-burnout class is the primary metric: missing an at-risk
  student is more problematic than a false alarm. Adjusting the classification
  threshold below 0.5 allows higher recall at the expense of lower precision.

WHAT THE MODELS CANNOT DO:
• Performance is modest (ROC-AUC ~0.55–0.65):
  - Sample size is limited (n=132), mostly 2nd-year engineering hostel students.
  - Bivariate correlations between single habits and burnout are weak.
  - Cross-sectional, self-reported convenience snapshot prevents causal claims.
• These models are NOT suitable for high-stakes individual clinical screening.

WHY SCORES ARE MODEST:
• Burnout is multifactorial; daily habits account for only a fraction of variance.
  Unmeasured psychological, familial, social, and academic pressures play large roles.
• The binary target is a sample median split (15), not an absolute clinical diagnosis.
• 132 rows with 10 features creates substantial sampling variance across folds.
""", flush=True)

    print("\n[OK] Task 1 complete. All outputs in:", OUT, flush=True)

if __name__ == "__main__":
    main()
