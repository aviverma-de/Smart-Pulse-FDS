"""
SmartPulse Validation Routers
Endpoints for consent, anonymous data deletion, student feedback, verified outcomes,
and admin-gated validation metrics.
"""

import json
import uuid
import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.orm import Session

from .. import config
from ..db import (
    get_db,
    Student,
    Assessment,
    Prediction,
    StudentFeedback,
    VerifiedOutcome,
    ModelVersion,
    ModelEvaluation
)
from ..models import (
    ConsentRequest,
    ConsentResponse,
    FeedbackRequest,
    FeedbackResponse,
    OutcomeRequest,
    OutcomeResponse
)
from ..metrics import (
    compute_classification_metrics,
    compute_regression_metrics,
    compute_feedback_analytics,
    compute_error_analysis,
    wilson_score_interval
)
from ..model_loader import container

router = APIRouter(tags=["validation"])

def verify_admin_auth(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    token = x_admin_token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    if not config.ADMIN_TOKEN or token != config.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required. Invalid or missing admin token."
        )
    return True

# ── Student Privacy & Consent ──────────────────────────────────────────────

@router.post("/api/consent", response_model=ConsentResponse)
def create_student_consent(payload: ConsentRequest, db: Session = Depends(get_db)):
    if not payload.consent:
        raise HTTPException(status_code=400, detail="Consent must be true to initialize an anonymous record.")

    anon_id = f"anon_{uuid.uuid4().hex[:12]}"
    return_code = f"SP-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"

    student = Student(
        id=anon_id,
        return_code=return_code,
        consent_given=True,
        created_at=datetime.datetime.utcnow()
    )
    db.add(student)
    db.commit()

    return ConsentResponse(
        anon_id=anon_id,
        return_code=return_code,
        consent_given=True,
        created_at=student.created_at.isoformat(),
        message="Consent recorded. Use this return code to complete your outcome check later."
    )

@router.delete("/api/data/{anon_id}")
def delete_student_data(anon_id: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(
        (Student.id == anon_id) | (Student.return_code == anon_id)
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"No student record found with ID/code {anon_id}")

    actual_id = student.id
    db.delete(student)
    db.commit()

    return {
        "status": "deleted",
        "anon_id": actual_id,
        "message": "All student assessments, predictions, feedback, and outcomes have been permanently erased."
    }

# ── Student Feedback (Subjective, Not Ground Truth) ─────────────────────────

@router.post("/api/feedback", response_model=FeedbackResponse)
def submit_student_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)):
    student_id = None
    prediction_id = payload.prediction_id

    if payload.return_code:
        st = db.query(Student).filter_by(return_code=payload.return_code).first()
        if st:
            student_id = st.id
    elif payload.anon_id:
        st = db.query(Student).filter_by(id=payload.anon_id).first()
        if st:
            student_id = st.id

    if not student_id:
        raise HTTPException(status_code=403, detail="Valid consent and anonymous return code are required to store feedback.")

    # If prediction_id not provided but student found, find latest prediction
    if not prediction_id and student_id:
        latest_pred = db.query(Prediction).filter_by(student_id=student_id).order_by(Prediction.id.desc()).first()
        if latest_pred:
            prediction_id = latest_pred.id

    prediction = db.query(Prediction).filter_by(id=prediction_id, student_id=student_id).first() if prediction_id else None
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found for this anonymous record.")

    fb = StudentFeedback(
        prediction_id=prediction_id,
        student_id=student_id,
        agreement=payload.agreement,
        score_feels_right=payload.score_feels_right,
        comment=payload.comment,
        is_demo=False,
        created_at=datetime.datetime.utcnow()
    )
    db.add(fb)
    db.commit()

    return FeedbackResponse(
        status="recorded",
        feedback_id=fb.id,
        agreement=fb.agreement,
        is_ground_truth=False,
        message="Subjective feedback recorded. Stored separately and labeled 'not ground truth'."
    )

# ── Verified Outcome Instrument ───────────────────────────────────────────

@router.post("/api/outcome", response_model=OutcomeResponse)
def submit_verified_outcome(payload: OutcomeRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter_by(return_code=payload.return_code).first()
    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Return code '{payload.return_code}' not recognized. Please check your code."
        )

    # Validate items 1..5
    for item_name, val in [("bo1", payload.bo1), ("bo2", payload.bo2), ("bo3", payload.bo3), ("bo4", payload.bo4), ("bo5", payload.bo5)]:
        if val < 1 or val > 5:
            raise HTTPException(status_code=400, detail=f"Question {item_name} must be between 1 and 5.")

    # Reuses EXACT instrument scoring and threshold logic from Cleaned_Data
    # burnout_total = sum(bo1..bo5), range 5-25
    # burnout_high = High if score >= 15 else Low
    measured_score = float(payload.bo1 + payload.bo2 + payload.bo3 + payload.bo4 + payload.bo5)
    measured_category = "High Risk" if measured_score >= 15.0 else "Low Risk"

    latest_assessment = db.query(Assessment).filter_by(student_id=student.id).order_by(Assessment.id.desc()).first()
    days_after = payload.days_after_assessment or 0.0
    if latest_assessment and days_after == 0.0:
        elapsed_sec = (datetime.datetime.utcnow() - latest_assessment.created_at).total_seconds()
        days_after = max(0.0, round(elapsed_sec / 86400.0, 2))

    outcome = VerifiedOutcome(
        student_id=student.id,
        assessment_id=latest_assessment.id if latest_assessment else None,
        bo1=payload.bo1,
        bo2=payload.bo2,
        bo3=payload.bo3,
        bo4=payload.bo4,
        bo5=payload.bo5,
        measured_score=measured_score,
        measured_category=measured_category,
        days_after_assessment=days_after,
        is_demo=False,
        created_at=datetime.datetime.utcnow()
    )
    db.add(outcome)
    db.commit()

    return OutcomeResponse(
        status="recorded",
        outcome_id=outcome.id,
        measured_score=measured_score,
        measured_category=measured_category,
        return_code=student.return_code,
        is_demo=outcome.is_demo,
        message="Independent verified outcome scored and saved using the original 5-item scale."
    )

# ── Admin-Gated Validation Metrics Endpoints ──────────────────────────────

def _get_validation_pairs(db: Session, include_demo: bool = False):
    query = db.query(VerifiedOutcome, Prediction, Assessment).join(
        Assessment, VerifiedOutcome.assessment_id == Assessment.id
    ).join(
        Prediction, Prediction.assessment_id == Assessment.id
    )
    if not include_demo:
        query = query.filter(VerifiedOutcome.is_demo == False)

    pairs = query.all()
    return pairs

@router.get("/api/validation/summary")
def get_validation_summary(
    include_demo: bool = Query(False),
    authenticated: bool = Depends(verify_admin_auth),
    db: Session = Depends(get_db)
):
    pairs = _get_validation_pairs(db, include_demo=include_demo)
    n = len(pairs)
    min_n = config.MIN_VALIDATION_N

    # Feedbacks count
    fb_q = db.query(StudentFeedback)
    if not include_demo:
        fb_q = fb_q.filter(StudentFeedback.is_demo == False)
    feedbacks = fb_q.all()
    n_fb = len(feedbacks)

    if n == 0:
        return {
            "status": "not_established",
            "message": "Not yet established (n=0)",
            "n": 0,
            "min_n": min_n,
            "is_low_sample": True,
            "progress_pct": 0.0,
            "include_demo": include_demo,
            "active_version": container.active_version,
            "classification": {"accuracy": None, "accuracy_ci": None, "macro_f1": None, "high_burnout_recall": None},
            "regression": {"mae": None, "mae_ci": None, "rmse": None, "r2": None},
            "feedback": {"agreement_pct": None, "agreement_ci": None, "n": n_fb}
        }

    y_true_cls = [p[0].measured_category for p in pairs]
    y_pred_cls = [p[1].category for p in pairs]
    regression_pairs = [p for p in pairs if p[1].score is not None]
    y_true_reg = [p[0].measured_score for p in regression_pairs]
    y_pred_reg = [p[1].score for p in regression_pairs]

    cls_m = compute_classification_metrics(y_true_cls, y_pred_cls, min_n=min_n)
    reg_m = compute_regression_metrics(y_true_reg, y_pred_reg, min_n=min_n)

    fb_items = [{"agreement": f.agreement} for f in feedbacks]
    fb_m = compute_feedback_analytics(fb_items)

    return {
        "status": "ready",
        "n": n,
        "min_n": min_n,
        "is_low_sample": n < min_n,
        "progress_pct": min(100.0, round((n / float(min_n)) * 100.0, 1)),
        "include_demo": include_demo,
        "active_version": container.active_version,
        "classification": {
            "accuracy": cls_m["accuracy"],
            "accuracy_ci": cls_m["accuracy_ci"],
            "macro_f1": cls_m["macro_f1"],
            "high_burnout_recall": cls_m["high_burnout_recall"],
            "high_burnout_recall_ci": cls_m["high_burnout_recall_ci"]
        },
        "regression": {
            "mae": reg_m["mae"],
            "mae_ci": reg_m["mae_ci"],
            "rmse": reg_m["rmse"],
            "r2": reg_m["r2"],
            "r2_ci": reg_m["r2_ci"]
        },
        "feedback": {
            "agreement_pct": fb_m.get("agreement_percentage"),
            "agreement_ci": fb_m.get("agreement_ci"),
            "n": n_fb
        }
    }

@router.get("/api/validation/classification")
def get_validation_classification(
    include_demo: bool = Query(False),
    authenticated: bool = Depends(verify_admin_auth),
    db: Session = Depends(get_db)
):
    pairs = _get_validation_pairs(db, include_demo=include_demo)
    y_true = [p[0].measured_category for p in pairs]
    y_pred = [p[1].category for p in pairs]

    res = compute_classification_metrics(y_true, y_pred, min_n=config.MIN_VALIDATION_N)
    res["include_demo"] = include_demo
    res["active_version"] = container.active_version
    return res

@router.get("/api/validation/regression")
def get_validation_regression(
    include_demo: bool = Query(False),
    authenticated: bool = Depends(verify_admin_auth),
    db: Session = Depends(get_db)
):
    pairs = _get_validation_pairs(db, include_demo=include_demo)
    regression_pairs = [p for p in pairs if p[1].score is not None]
    y_true = [p[0].measured_score for p in regression_pairs]
    y_pred = [p[1].score for p in regression_pairs]

    res = compute_regression_metrics(y_true, y_pred, min_n=config.MIN_VALIDATION_N)
    res["include_demo"] = include_demo
    res["active_version"] = container.active_version
    return res

@router.get("/api/validation/feedback")
def get_validation_feedback(
    include_demo: bool = Query(False),
    authenticated: bool = Depends(verify_admin_auth),
    db: Session = Depends(get_db)
):
    fb_q = db.query(StudentFeedback)
    if not include_demo:
        fb_q = fb_q.filter(StudentFeedback.is_demo == False)
    feedbacks = fb_q.all()

    # Match feedback to outcome to determine correctness
    fb_data = []
    for f in feedbacks:
        is_correct = None
        if f.student_id:
            outcome = db.query(VerifiedOutcome).filter_by(student_id=f.student_id).order_by(VerifiedOutcome.id.desc()).first()
            pred = db.query(Prediction).filter_by(student_id=f.student_id).order_by(Prediction.id.desc()).first()
            if outcome and pred:
                is_correct = (outcome.measured_category.strip().lower() == pred.category.strip().lower())
        fb_data.append({
            "agreement": f.agreement,
            "score_feels_right": f.score_feels_right,
            "comment": f.comment,
            "is_correct": is_correct
        })

    res = compute_feedback_analytics(fb_data)
    res["include_demo"] = include_demo
    return res

@router.get("/api/validation/errors")
def get_validation_errors(
    include_demo: bool = Query(False),
    authenticated: bool = Depends(verify_admin_auth),
    db: Session = Depends(get_db)
):
    pairs = _get_validation_pairs(db, include_demo=include_demo)
    records = []
    for outcome, pred, assessment in pairs:
        try:
            inputs = json.loads(assessment.inputs_json)
        except:
            inputs = {}
        records.append({
            "id": outcome.id,
            "actual_cat": outcome.measured_category,
            "pred_cat": pred.category,
            "actual_score": outcome.measured_score,
            "pred_score": pred.score,
            "inputs": inputs
        })

    res = compute_error_analysis(records)
    res["include_demo"] = include_demo
    return res

@router.get("/api/validation/models")
def get_validation_models(
    authenticated: bool = Depends(verify_admin_auth),
    db: Session = Depends(get_db)
):
    versions = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()
    evals = db.query(ModelEvaluation).order_by(ModelEvaluation.created_at.desc()).all()

    eval_map = {}
    for ev in evals:
        if ev.version not in eval_map:
            try:
                eval_map[ev.version] = json.loads(ev.metrics_json)
            except:
                eval_map[ev.version] = {}

    results = []
    for v in versions:
        results.append({
            "version": v.version,
            "is_active": v.is_active,
            "parent": v.parent,
            "training_rows": v.training_rows,
            "created_at": v.created_at.isoformat(),
            "evaluation": eval_map.get(v.version, {})
        })

    return {
        "active_version": container.active_version,
        "models": results
    }
