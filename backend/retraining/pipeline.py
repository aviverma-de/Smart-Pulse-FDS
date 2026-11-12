"""
SmartPulse Controlled Retraining Pipeline
Flow: Gather verified data -> Check adequacy -> Train candidates on (Original Train + Verified Consented Non-Demo)
      -> Evaluate on FROZEN held-out test set -> Apply strict promotion criteria -> Promote or Reject with report.
"""

import os
import json
import datetime
import pathlib
import numpy as np
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import RepeatedStratifiedKFold, cross_val_score
from sklearn.metrics import f1_score, recall_score, mean_absolute_error, accuracy_score, precision_score

from .frozen_test import load_frozen_test_df, load_initial_train_df
try:
    from app import config
    from app.db import SessionLocal, ModelVersion, ModelEvaluation, VerifiedOutcome, Assessment, Student
    from app.metrics import wilson_score_interval, bootstrap_ci
except ImportError:
    try:
        from backend.app import config
        from backend.app.db import SessionLocal, ModelVersion, ModelEvaluation, VerifiedOutcome, Assessment, Student
        from backend.app.metrics import wilson_score_interval, bootstrap_ci
    except ImportError:
        from ..app import config
        from ..app.db import SessionLocal, ModelVersion, ModelEvaluation, VerifiedOutcome, Assessment, Student
        from ..app.metrics import wilson_score_interval, bootstrap_ci

FEATURES = [
    "sleep_mid_hrs", "sleep_quality", "bedtime_code",
    "screen_mid_hrs", "phone_bed_code",
    "exercise_days_mid", "deadlines_code",
    "workload_code", "performance_code"
]
FEATURES_FINAL = FEATURES + ["performance_missing"]

def prepare_feature_row(inputs_dict: dict) -> dict:
    row = {f: float(inputs_dict.get(f, 0.0)) for f in FEATURES}
    # Check if performance_code is None or missing
    perf = inputs_dict.get("performance_code")
    if perf is None or pd.isna(perf):
        row["performance_code"] = np.nan
        row["performance_missing"] = 1.0
    else:
        row["performance_code"] = float(perf)
        row["performance_missing"] = 0.0
    return row

def get_retraining_data(include_demo: bool = False) -> Tuple_Data:
    """
    Combines initial 105-row training data with all verified, consented, non-demo outcomes.
    Frozen 27-row test set is STRICTLY EXCLUDED.
    """
    initial_train_df = load_initial_train_df()
    
    # Query database for verified outcomes
    db = SessionLocal()
    try:
        query = db.query(VerifiedOutcome, Assessment).join(
            Assessment, VerifiedOutcome.assessment_id == Assessment.id
        ).join(Student, VerifiedOutcome.student_id == Student.id).filter(
            VerifiedOutcome.is_demo == False,
            Student.consent_given == True
        )

        records = query.all()
        new_rows = []
        dropped_count = 0

        for outcome, assessment in records:
            try:
                inputs = json.loads(assessment.inputs_json)
                feat_row = prepare_feature_row(inputs)
                feat_row["burnout_total"] = float(outcome.measured_score)
                feat_row["burnout_high"] = 1 if outcome.measured_score >= 15.0 else 0
                new_rows.append(feat_row)
            except Exception as e:
                dropped_count += 1

        if new_rows:
            new_df = pd.DataFrame(new_rows)
            # Combine initial train with new verified data
            combined_df = pd.concat([initial_train_df, new_df], ignore_index=True)
        else:
            combined_df = initial_train_df

        return combined_df, len(new_rows), dropped_count
    finally:
        db.close()

class Tuple_Data:
    def __init__(self, df, new_count, dropped_count):
        self.df = df
        self.new_count = new_count
        self.dropped_count = dropped_count

def build_classifier_pipeline(model_type="rf", **params):
    numeric_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    preprocessor = ColumnTransformer(
        transformers=[("num", numeric_transformer, FEATURES_FINAL)],
        remainder="drop",
    )
    if model_type == "rf":
        clf = RandomForestClassifier(
            n_estimators=params.get("n_estimators", 300),
            max_depth=params.get("max_depth", 5),
            min_samples_leaf=params.get("min_samples_leaf", 3),
            random_state=config.SEED,
            n_jobs=1
        )
    elif model_type == "lr":
        clf = LogisticRegression(
            penalty="l2",
            C=params.get("C", 0.5),
            solver="lbfgs",
            max_iter=1000,
            random_state=config.SEED
        )
    elif model_type == "gb":
        clf = GradientBoostingClassifier(
            n_estimators=params.get("n_estimators", 150),
            learning_rate=params.get("learning_rate", 0.05),
            max_depth=params.get("max_depth", 3),
            random_state=config.SEED
        )
    else:
        raise ValueError(f"Unknown classifier: {model_type}")

    return Pipeline([("pre", preprocessor), ("clf", clf)])

def build_regressor_pipeline(model_type="rf", **params):
    numeric_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    preprocessor = ColumnTransformer(
        transformers=[("num", numeric_transformer, FEATURES_FINAL)],
        remainder="drop",
    )
    if model_type == "rf":
        reg = RandomForestRegressor(
            n_estimators=params.get("n_estimators", 200),
            max_depth=params.get("max_depth", 4),
            random_state=config.SEED,
            n_jobs=1
        )
    elif model_type == "ridge":
        reg = Ridge(alpha=params.get("alpha", 1.0), random_state=config.SEED)
    else:
        raise ValueError(f"Unknown regressor: {model_type}")

    return Pipeline([("pre", preprocessor), ("reg", reg)])

def evaluate_on_frozen_test(clf_pipeline, reg_pipeline=None, reference_pipeline=None):
    """
    Evaluates pipelines strictly on the 27-row frozen held-out test set.
    """
    test_df = load_frozen_test_df().copy()
    test_df["performance_missing"] = test_df["performance_code"].isnull().astype(float)

    X_test = test_df[FEATURES_FINAL]
    y_test_class = test_df["burnout_high"].values.astype(int)
    y_test_reg = test_df["burnout_total"].values.astype(float)

    # Classification metrics
    preds_class = clf_pipeline.predict(X_test)
    acc = accuracy_score(y_test_class, preds_class)
    f1 = f1_score(y_test_class, preds_class, average="macro")
    f1_gain_ci = None
    if reference_pipeline is not None:
        reference_predictions = reference_pipeline.predict(X_test)
        rng = np.random.RandomState(config.SEED)
        gains = []
        for _ in range(2000):
            idx = rng.randint(0, len(y_test_class), size=len(y_test_class))
            gains.append(
                f1_score(y_test_class[idx], preds_class[idx], average="macro", zero_division=0)
                - f1_score(y_test_class[idx], reference_predictions[idx], average="macro", zero_division=0)
            )
        f1_gain_ci = [round(float(x), 4) for x in np.percentile(gains, [2.5, 97.5])]
    recall_high = recall_score(y_test_class, preds_class, pos_label=1)
    prec_high = precision_score(y_test_class, preds_class, pos_label=1, zero_division=0)

    # CIs on test set (n=27)
    acc_ci = wilson_score_interval(int(np.sum(y_test_class == preds_class)), len(y_test_class))
    high_tp = int(np.sum((y_test_class == 1) & (preds_class == 1)))
    high_total = int(np.sum(y_test_class == 1))
    recall_ci = wilson_score_interval(high_tp, high_total)

    reg_metrics = {}
    if reg_pipeline is not None:
        preds_reg = reg_pipeline.predict(X_test)
        mae = mean_absolute_error(y_test_reg, preds_reg)
        rmse = np.sqrt(np.mean((y_test_reg - preds_reg) ** 2))
        mae_ci = bootstrap_ci(list(y_test_reg), list(preds_reg), metric_type="mae")
        reg_metrics = {
            "mae": round(float(mae), 4),
            "mae_ci": mae_ci,
            "rmse": round(float(rmse), 4)
        }

    return {
        "n_test": len(test_df),
        "accuracy": round(float(acc), 4),
        "accuracy_ci": acc_ci,
        "macro_f1": round(float(f1), 4),
        "f1_gain_ci": f1_gain_ci,
        "high_recall": round(float(recall_high), 4),
        "high_recall_ci": recall_ci,
        "high_precision": round(float(prec_high), 4),
        "regression": reg_metrics
    }

def run_retraining_pipeline(
    force: bool = False,
    include_demo: bool = False,
    candidate_name: str = "Candidate-RF-Optimized"
) -> Dict[str, Any]:
    """
    Controlled Retraining Pipeline:
    1. Loads combined training set (Initial 105 rows + Verified non-demo outcomes)
    2. Enforces MIN_RETRAIN_OUTCOMES requirement unless force=True
    3. Trains and CV-evaluates candidate architectures
    4. Evaluates Active model vs Candidate on FROZEN 27-row held-out test set
    5. Validates promotion criteria:
       - Candidate macro_f1 >= active_f1 + MIN_F1_MARGIN
       - Candidate high_recall >= active_high_recall
       - Gain exceeds CI noise
    6. Promotes to new version or records explicit rejection reasons
    7. Generates markdown report in docs/retraining-reports/
    """
    train_df, new_verified_count, dropped_count = get_retraining_data(include_demo=include_demo)
    train_df = train_df.copy()

    # Check minimum required outcomes
    if new_verified_count < config.MIN_RETRAIN_OUTCOMES and not force:
        needed = config.MIN_RETRAIN_OUTCOMES - new_verified_count
        return {
            "status": "refused",
            "reason": "insufficient_verified_outcomes",
            "message": f"Retraining refused: Found {new_verified_count} verified outcomes, but at least {config.MIN_RETRAIN_OUTCOMES} are required.",
            "current_verified_count": new_verified_count,
            "needed_count": needed,
            "min_required": config.MIN_RETRAIN_OUTCOMES
        }

    train_df["performance_missing"] = train_df["performance_code"].isnull().astype(float)
    X_train = train_df[FEATURES_FINAL]
    y_train_class = train_df["burnout_high"].values.astype(int)
    y_train_reg = train_df["burnout_total"].values.astype(float)

    # 1. Evaluate Current Active Model on Frozen Test Set
    try:
        from app.model_loader import container
    except ImportError:
        try:
            from backend.app.model_loader import container
        except ImportError:
            from ..app.model_loader import container
    active_eval = evaluate_on_frozen_test(container.pipe_rf)

    # 2. Train Candidates with Repeated Stratified K-Fold CV
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=config.SEED)
    
    candidates = [
        ("Candidate-RF-300", "rf", {"n_estimators": 300, "max_depth": 5, "min_samples_leaf": 3}),
        ("Candidate-RF-150", "rf", {"n_estimators": 150, "max_depth": 4, "min_samples_leaf": 4}),
        ("Candidate-LR-L2", "lr", {"C": 0.5}),
        ("Candidate-GBM", "gb", {"n_estimators": 100, "learning_rate": 0.05, "max_depth": 3}),
    ]

    best_cand_name = None
    best_cand_pipe = None
    best_cand_reg_pipe = None
    best_cv_f1 = -1.0

    cv_results = {}
    for name, mtype, params in candidates:
        clf_pipe = build_classifier_pipeline(model_type=mtype, **params)
        scores = cross_val_score(clf_pipe, X_train, y_train_class, cv=cv, scoring="f1_macro")
        mean_cv_f1 = float(np.mean(scores))
        cv_results[name] = round(mean_cv_f1, 4)
        if mean_cv_f1 > best_cv_f1:
            best_cv_f1 = mean_cv_f1
            best_cand_name = name
            # Fit on full retraining set
            clf_pipe.fit(X_train, y_train_class)
            best_cand_pipe = clf_pipe

    # Build regressor companion
    reg_pipe = build_regressor_pipeline(model_type="rf", n_estimators=200, max_depth=4)
    reg_pipe.fit(X_train, y_train_reg)
    best_cand_reg_pipe = reg_pipe

    # 3. Evaluate Best Candidate on Frozen Test Set
    candidate_eval = evaluate_on_frozen_test(best_cand_pipe, best_cand_reg_pipe, container.pipe_rf)

    # 4. Promotion Criteria Check
    # Must beat active on macro_f1 by MIN_F1_MARGIN and NOT lower high_burnout_recall
    active_f1 = active_eval["macro_f1"]
    cand_f1 = candidate_eval["macro_f1"]
    active_recall = active_eval["high_recall"]
    cand_recall = candidate_eval["high_recall"]

    f1_gain = cand_f1 - active_f1
    recall_diff = cand_recall - active_recall

    rejection_reasons = []
    if f1_gain < config.MIN_F1_MARGIN:
        rejection_reasons.append(
            f"Macro-F1 gain ({f1_gain:+.4f}) did not achieve required margin of +{config.MIN_F1_MARGIN:.4f} (Active: {active_f1:.4f}, Candidate: {cand_f1:.4f})."
        )
    f1_gain_ci = candidate_eval.get("f1_gain_ci")
    if not f1_gain_ci or f1_gain_ci[0] <= 0:
        rejection_reasons.append("Macro-F1 gain does not exceed paired-bootstrap 95% CI noise on the frozen test set.")
    if recall_diff < -1e-4:
        rejection_reasons.append(
            f"High-burnout recall dropped from {active_recall:.4f} to {cand_recall:.4f} (Recall cannot decrease)."
        )

    is_promoted = (len(rejection_reasons) == 0)

    db = SessionLocal()
    try:
        active_version_record = db.query(ModelVersion).filter_by(is_active=True).first()
        active_ver_str = active_version_record.version if active_version_record else "v1.0"

        # Version numbering
        if is_promoted:
            # Generate next version tag: v1.1, v1.2, etc.
            all_versions = db.query(ModelVersion.version).all()
            ver_nums = []
            for (v,) in all_versions:
                if v.startswith("v1."):
                    try: ver_nums.append(int(v.split(".")[1]))
                    except: pass
            next_sub = max(ver_nums, default=0) + 1
            new_version_str = f"v1.{next_sub}"

            # Save models to disk
            model_save_dir = config.SAVED_MODELS_DIR
            clf_path = model_save_dir / f"{new_version_str}_pipe_rf.joblib"
            reg_path = model_save_dir / f"{new_version_str}_reg_rf.joblib"
            joblib.dump(best_cand_pipe, clf_path)
            joblib.dump(best_cand_reg_pipe, reg_path)

            # Deactivate previous active model
            if active_version_record:
                active_version_record.is_active = False

            # Create new model version record
            new_ver = ModelVersion(
                version=new_version_str,
                path=str(clf_path),
                is_active=True,
                parent=active_ver_str,
                training_rows=len(train_df),
                features=json.dumps(FEATURES_FINAL),
                created_at=datetime.datetime.utcnow()
            )
            db.add(new_ver)

            # Record evaluation
            eval_record = ModelEvaluation(
                version=new_version_str,
                n=candidate_eval["n_test"],
                metrics_json=json.dumps(candidate_eval),
                created_at=datetime.datetime.utcnow()
            )
            db.add(eval_record)
            db.commit()

            # Hot-swap live container models
            container.pipe_rf = best_cand_pipe
            container.active_version = new_version_str
        else:
            new_version_str = f"candidate_rejected_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            eval_record = ModelEvaluation(
                version=new_version_str,
                n=candidate_eval["n_test"],
                metrics_json=json.dumps({
                    "candidate_eval": candidate_eval,
                    "rejection_reasons": rejection_reasons
                }),
                created_at=datetime.datetime.utcnow()
            )
            db.add(eval_record)
            db.commit()

        # Generate markdown audit report
        config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report_filename = f"report-{new_version_str}.md"
        report_path = config.REPORTS_DIR / report_filename

        report_content = f"""# SmartPulse Model Retraining Report: {new_version_str}
- **Timestamp**: {datetime.datetime.utcnow().isoformat()}Z
- **Decision**: {'PROMOTED' if is_promoted else 'REJECTED'}
- **Parent Version**: {active_ver_str}
- **Training Samples**: {len(train_df)} ({len(load_initial_train_df())} original + {new_verified_count} verified new outcomes)
- **Data Exclusions**: {dropped_count} malformed rows dropped during cleaning
- **Frozen Test Set**: Exactly 27 rows (stratified seed=42, untouched)

## Performance Comparison on Frozen Held-Out Test Set (n=27)
| Metric | Active ({active_ver_str}) | Candidate ({best_cand_name}) | Difference | Criteria Met? |
| :--- | :--- | :--- | :--- | :--- |
| **Accuracy** | {active_eval['accuracy']:.4f} | {candidate_eval['accuracy']:.4f} | {candidate_eval['accuracy'] - active_eval['accuracy']:+.4f} | — |
| **Macro-F1** | {active_eval['macro_f1']:.4f} | {candidate_eval['macro_f1']:.4f} | {f1_gain:+.4f} | {'YES' if f1_gain >= config.MIN_F1_MARGIN else 'NO (Gain < Margin)'} |
| **High-Burnout Recall** | {active_eval['high_recall']:.4f} | {candidate_eval['high_recall']:.4f} | {recall_diff:+.4f} | {'YES' if recall_diff >= -1e-4 else 'NO (Recall lowered)'} |
| **High-Burnout Precision** | {active_eval['high_precision']:.4f} | {candidate_eval['high_precision']:.4f} | {candidate_eval['high_precision'] - active_eval['high_precision']:+.4f} | — |

## Cross-Validation Scores on Training Set (RepeatedStratifiedKFold)
{json.dumps(cv_results, indent=2)}

## Decision Details
{('Candidate model outperformed active model across required criteria and is now active.' if is_promoted else 'Candidate model was REJECTED due to: ' + '; '.join(rejection_reasons))}
"""
        with open(report_path, "w", encoding="utf-8") as rf:
            rf.write(report_content)

        return {
            "status": "promoted" if is_promoted else "rejected",
            "version": new_version_str,
            "active_version": active_ver_str if not is_promoted else new_version_str,
            "is_promoted": is_promoted,
            "training_rows": len(train_df),
            "new_verified_count": new_verified_count,
            "candidate_name": best_cand_name,
            "f1_gain": round(f1_gain, 4),
            "recall_difference": round(recall_diff, 4),
            "active_evaluation": active_eval,
            "candidate_evaluation": candidate_eval,
            "rejection_reasons": rejection_reasons,
            "report_file": str(report_path.name)
        }

    finally:
        db.close()

def rollback_model_to_version(target_version: str) -> Dict[str, Any]:
    """
    Rolls back the active model to a previous version (e.g. 'v1.0').
    Never overwrites v1.0. Updates database and hot-swaps memory container.
    """
    db = SessionLocal()
    try:
        target = db.query(ModelVersion).filter_by(version=target_version).first()
        if not target:
            return {"success": False, "message": f"Version {target_version} not found."}

        # Deactivate all versions
        db.query(ModelVersion).update({ModelVersion.is_active: False})
        target.is_active = True
        db.commit()

        # Hot swap in container
        try:
            from app.model_loader import container
        except ImportError:
            try:
                from backend.app.model_loader import container
            except ImportError:
                from ..app.model_loader import container
        if target_version == "v1.0":
            # Reload base v1.0 pipeline
            container.pipe_rf = joblib.load(config.SAVED_MODELS_DIR / "pipe_rf.joblib")
            container.pipe_lr = joblib.load(config.SAVED_MODELS_DIR / "pipe_lr.joblib")
        else:
            clf_path = pathlib.Path(target.path)
            if clf_path.exists():
                container.pipe_rf = joblib.load(clf_path)

        container.active_version = target_version
        return {
            "success": True,
            "active_version": target_version,
            "message": f"Successfully rolled back active model to {target_version}."
        }
    finally:
        db.close()
