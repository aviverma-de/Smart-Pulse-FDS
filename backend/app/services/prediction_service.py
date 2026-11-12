"""
SmartPulse Prediction & Attribution Service
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
from ..model_loader import container
from ..models import (
    AssessmentInput,
    PredictionResponse,
    ScoreResponse,
    WhatIfRequest,
    WhatIfResponse,
    WhatIfScenarioResult,
    ExplainResponse,
    FeatureContribution,
    TopFactorExplanation
)
from ..preprocessing import (
    assessment_to_dataframe,
    standardize_for_regression,
    compute_stress_total,
    FEATURE_LABELS
)
from .. import config

def predict_category(input_data: AssessmentInput) -> PredictionResponse:
    df_feat = assessment_to_dataframe(input_data)
    
    # Random Forest probability & class
    probs = container.pipe_rf.predict_proba(df_feat)[0]
    prob_low = float(probs[0])
    prob_high = float(probs[1])
    
    # 0.5 decision threshold
    pred_class = int(prob_high >= 0.5)
    category = "High Risk" if pred_class == 1 else "Low Risk"
    risk_label = "Elevated Burnout Risk" if pred_class == 1 else "Low / Baseline Risk"

    pred_id = None
    ret_code = input_data.return_code
    anon_id = input_data.anon_id

    # If consented student return_code or anon_id is present, store prediction linked to assessment
    if ret_code or anon_id:
        try:
            from ..db import SessionLocal, Student, Assessment, Prediction
            import json
            db = SessionLocal()
            try:
                student = None
                if ret_code:
                    student = db.query(Student).filter_by(return_code=ret_code).first()
                if not student and anon_id:
                    student = db.query(Student).filter_by(id=anon_id).first()

                if student:
                    ret_code = student.return_code
                    anon_id = student.id
                    # Record assessment
                    assessment = Assessment(
                        student_id=student.id,
                        inputs_json=json.dumps(input_data.model_dump(exclude={"anon_id", "return_code"}))
                    )
                    db.add(assessment)
                    db.flush()

                    # Record prediction
                    score_result = predict_score(input_data)
                    pred_record = Prediction(
                        assessment_id=assessment.id,
                        student_id=student.id,
                        model_version=container.active_version,
                        category=category,
                        probs=json.dumps({"low": round(prob_low, 4), "high": round(prob_high, 4)}),
                        score=score_result.predicted_score
                    )
                    db.add(pred_record)
                    db.commit()
                    pred_id = pred_record.id
            finally:
                db.close()
        except Exception as e:
            print("Warning: Failed to persist prediction record:", e)

    return PredictionResponse(
        category=category,
        risk_label=risk_label,
        probabilities={
            "low": round(prob_low, 4),
            "high": round(prob_high, 4)
        },
        model_used=f"Random Forest Classifier ({container.active_version})",
        threshold=0.5,
        disclaimer=config.DISCLAIMER_TEXT,
        model_version=container.active_version,
        prediction_id=pred_id,
        return_code=ret_code,
        anon_id=anon_id
    )

def predict_score(input_data: AssessmentInput) -> ScoreResponse:
    df_feat = assessment_to_dataframe(input_data)
    z_matrix = standardize_for_regression(
        df_feat,
        container.meta["means"],
        container.meta["stds"],
        container.meta["perf_median"]
    )

    # Use Bayesian regression formula from outputs/bayes_summary.csv
    # Intercept = 14.9743, sigma = 3.6934
    bayes_dict = {item["feature"]: item["posterior_mean"] for item in container.bayes_params}
    intercept = bayes_dict.get("intercept", container.meta["ols_intercept"])
    sigma = bayes_dict.get("sigma", 3.6934)

    # Compute dot product
    score_est = intercept
    cols = container.meta["features_final"]
    for idx, col in enumerate(cols):
        beta = bayes_dict.get(col, container.meta["ols_coefs"].get(col, 0.0))
        score_est += beta * z_matrix[0, idx]

    # Bound within realistic theoretical scale [5, 25]
    score_clamped = max(5.0, min(25.0, score_est))
    
    # 94% HDI margin: ~1.88 * sigma
    hdi_lower = max(5.0, score_clamped - 1.88 * sigma)
    hdi_upper = min(25.0, score_clamped + 1.88 * sigma)

    # Percentile relative to real 132 student dataset
    percentile = 50.0
    if container.df_raw is not None and "burnout_total" in container.df_raw.columns:
        percentile = float((container.df_raw["burnout_total"] < score_clamped).mean() * 100)

    # Optional stress calculation
    calc_stress = compute_stress_total(input_data)

    if input_data.return_code or input_data.anon_id:
        try:
            from ..db import SessionLocal, Student, Prediction
            db = SessionLocal()
            try:
                st = None
                if input_data.return_code:
                    st = db.query(Student).filter_by(return_code=input_data.return_code).first()
                if not st and input_data.anon_id:
                    st = db.query(Student).filter_by(id=input_data.anon_id).first()
                if st:
                    pred = db.query(Prediction).filter_by(student_id=st.id).order_by(Prediction.id.desc()).first()
                    if pred:
                        pred.score = round(score_clamped, 2)
                        db.commit()
            finally:
                db.close()
        except Exception:
            pass

    return ScoreResponse(
        predicted_score=round(score_clamped, 2),
        credible_interval_94=[round(hdi_lower, 2), round(hdi_upper, 2)],
        scale_min=int(container.meta.get("burnout_min", 5)),
        scale_max=int(container.meta.get("burnout_max", 25)),
        percentile=round(percentile, 1),
        calculated_stress_total=calc_stress,
        disclaimer=config.DISCLAIMER_TEXT
    )

def explain_prediction(input_data: AssessmentInput) -> ExplainResponse:
    df_feat = assessment_to_dataframe(input_data)
    
    # Compute standardized features
    z_matrix = standardize_for_regression(
        df_feat,
        container.meta["means"],
        container.meta["stds"],
        container.meta["perf_median"]
    )
    
    # Use Logistic Regression coefficients * standardized features (real log-odds attribution)
    lr_clf = container.pipe_lr.named_steps["clf"]
    coefs = lr_clf.coef_[0]
    cols = container.meta["features_final"]
    
    contributions: List[FeatureContribution] = []
    for idx, col in enumerate(cols):
        val = df_feat[col].iloc[0]
        if hasattr(val, "item"):
            val = val.item()
        if pd.isna(val):
            val_clean = "Not taken"
        elif isinstance(val, float):
            val_clean = round(float(val), 2)
        elif isinstance(val, int):
            val_clean = int(val)
        else:
            val_clean = str(val)

        contrib = float(coefs[idx] * z_matrix[0, idx])
        direction = "increases_risk" if contrib > 0 else "decreases_risk"
        
        contributions.append(FeatureContribution(
            feature=col,
            label=FEATURE_LABELS.get(col, col),
            user_value=val_clean,
            contribution=round(contrib, 4),
            direction=direction
        ))

    # Sort by absolute contribution magnitude
    sorted_contribs = sorted(contributions, key=lambda c: abs(c.contribution), reverse=True)
    
    top_factors: List[TopFactorExplanation] = []
    for c in sorted_contribs[:4]:
        label = c.label
        val = c.user_value
        if c.feature == "workload_code":
            if val in [3, 4]:
                exp = f"Perceived heavy/overwhelming workload (+{abs(c.contribution):.2f} log-odds) is the strongest observed risk factor for burnout."
            else:
                exp = f"Reported manageable workload (-{abs(c.contribution):.2f} log-odds) provides strong buffer against academic burnout."
        elif c.feature == "phone_bed_code":
            if val in [3, 4]:
                exp = f"Frequent bedtime smartphone usage (+{abs(c.contribution):.2f} log-odds) is positively associated with higher cognitive fatigue."
            else:
                exp = f"Minimal phone use before bed (-{abs(c.contribution):.2f} log-odds) supports healthier wind-down cycles."
        elif c.feature == "bedtime_code":
            if val in [3, 4]:
                exp = f"Late sleep schedules past 1 AM (+{abs(c.contribution):.2f} log-odds) are associated with elevated burnout risk."
            else:
                exp = f"Earlier bedtimes (-{abs(c.contribution):.2f} log-odds) align with favorable sleep architecture."
        elif c.feature == "performance_code":
            if val in [1.0, 2.0]:
                exp = f"Performance falling below personal expectations (+{abs(c.contribution):.2f} log-odds) increases academic stress."
            else:
                exp = f"Satisfactory exam performance (-{abs(c.contribution):.2f} log-odds) reinforces academic self-efficacy."
        elif c.feature == "exercise_days_mid":
            exp = f"Reported exercise routine of {val} days/week contributed {c.contribution:+.2f} to the log-odds calculation."
        elif c.feature == "sleep_mid_hrs":
            exp = f"Reported nightly sleep duration of {val} hours contributed {c.contribution:+.2f} to the log-odds estimate."
        else:
            exp = f"{label} (value: {val}) contributed {c.contribution:+.2f} toward the model's standardized risk estimate."
            
        top_factors.append(TopFactorExplanation(
            feature=c.feature,
            label=c.label,
            impact_level="High Impact" if abs(c.contribution) >= 0.3 else "Moderate Impact",
            explanation=exp
        ))

    return ExplainResponse(
        method="Logistic Regression Standardized Feature Contribution (β_j * z_j log-odds decomposition)",
        contributions=sorted_contribs,
        top_factors=top_factors,
        disclaimer=config.DISCLAIMER_TEXT
    )

def simulate_whatif(request: WhatIfRequest) -> WhatIfResponse:
    base_cat = predict_category(request.baseline)
    base_score = predict_score(request.baseline)

    mod_cat = predict_category(request.modified)
    mod_score = predict_score(request.modified)

    diff = round(mod_score.predicted_score - base_score.predicted_score, 2)
    cat_changed = (base_cat.category != mod_cat.category)

    if diff < -0.1:
        direction = "improved"
    elif diff > 0.1:
        direction = "worsened"
    else:
        direction = "unchanged"

    return WhatIfResponse(
        baseline=WhatIfScenarioResult(
            score=base_score.predicted_score,
            category=base_cat.category,
            probabilities=base_cat.probabilities
        ),
        modified=WhatIfScenarioResult(
            score=mod_score.predicted_score,
            category=mod_cat.category,
            probabilities=mod_cat.probabilities
        ),
        score_difference=diff,
        category_changed=cat_changed,
        direction=direction,
        caution=config.WHATIF_CAUTION,
        disclaimer=config.DISCLAIMER_TEXT
    )
