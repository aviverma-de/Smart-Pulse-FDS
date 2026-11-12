"""
SmartPulse Admin Routers
Gated endpoints for model retraining, candidate promotion, rollback,
and demo data management.
"""

import json
import random
import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import config
from ..db import get_db, Student, Assessment, Prediction, StudentFeedback, VerifiedOutcome, ModelVersion
try:
    from retraining.pipeline import run_retraining_pipeline, rollback_model_to_version
except ImportError:
    try:
        from backend.retraining.pipeline import run_retraining_pipeline, rollback_model_to_version
    except ImportError:
        from ..retraining.pipeline import run_retraining_pipeline, rollback_model_to_version
from .validation import verify_admin_auth

router = APIRouter(prefix="/api/admin", tags=["admin"])

class RetrainRequest(BaseModel):
    force: Optional[bool] = False
    include_demo: Optional[bool] = False

class RollbackRequest(BaseModel):
    target_version: str

@router.post("/retrain")
def admin_retrain(
    payload: Optional[RetrainRequest] = None,
    authenticated: bool = Depends(verify_admin_auth)
):
    # Public admin requests cannot bypass the verified-outcome minimum.
    force = False
    include_demo = payload.include_demo if payload else False
    result = run_retraining_pipeline(force=force, include_demo=include_demo)
    return result

@router.post("/promote")
def admin_promote(
    authenticated: bool = Depends(verify_admin_auth)
):
    # Triggers retraining and automatically promotes if candidate passes all promotion criteria
    result = run_retraining_pipeline(force=False)
    return result

@router.post("/rollback")
def admin_rollback(
    payload: RollbackRequest,
    authenticated: bool = Depends(verify_admin_auth)
):
    result = rollback_model_to_version(payload.target_version)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result

@router.post("/seed-demo")
def admin_seed_demo(
    count: int = Query(35, ge=1, le=100),
    authenticated: bool = Depends(verify_admin_auth),
    db: Session = Depends(get_db)
):
    """
    Seeds realistic demo validation data flagged with is_demo=True.
    Used exclusively for testing the Validation Center UI.
    Excluded from real metrics and training.
    """
    from ..preprocessing import assessment_to_dataframe
    from ..model_loader import container
    from ..models import AssessmentInput

    random.seed(config.SEED + 101)
    np_rand = random.Random(config.SEED + 101)

    import uuid
    created_students = 0
    for i in range(count):
        anon_id = f"demo_anon_{uuid.uuid4().hex[:12]}"
        return_code = f"DEMO-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"

        student = Student(
            id=anon_id,
            return_code=return_code,
            consent_given=True,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(1, 20))
        )
        db.add(student)

        # Realistic feature generation
        sleep_h = random.choice([4.5, 5.5, 6.5, 7.5, 8.5])
        workload = random.choice([1, 2, 3, 4])
        phone = random.choice([1, 2, 3, 4])
        screen = random.choice([1.0, 3.0, 5.0, 7.0])
        exercise = random.choice([0.0, 1.5, 3.5, 5.5])
        deadlines = random.choice([1, 2, 3, 4])
        sleep_q = random.choice([1, 2, 3, 4, 5])
        bedtime = random.choice([1, 2, 3, 4])
        perf = random.choice([1.0, 2.0, 3.0, 4.0, 5.0, None])

        inp_dict = {
            "sleep_mid_hrs": sleep_h,
            "sleep_quality": sleep_q,
            "bedtime_code": bedtime,
            "screen_mid_hrs": screen,
            "phone_bed_code": phone,
            "exercise_days_mid": exercise,
            "deadlines_code": deadlines,
            "workload_code": workload,
            "performance_code": perf,
            "pss1_no_control": 3,
            "pss2_confident": 3,
            "pss3_going_my_way": 3,
            "pss4_piling_up": 3
        }

        assessment = Assessment(
            student_id=student.id,
            inputs_json=json.dumps(inp_dict),
            created_at=student.created_at
        )
        db.add(assessment)
        db.flush()

        # Run model inference to get prediction
        ainp = AssessmentInput(**inp_dict)
        df_feat = assessment_to_dataframe(ainp)
        probs = container.pipe_rf.predict_proba(df_feat)[0]
        prob_high = float(probs[1])
        cat = "High Risk" if prob_high >= 0.5 else "Low Risk"

        # Continuous prediction
        pred_score = 14.97 + (workload - 2.5) * 1.5 + (phone - 2.5) * 1.0 - (sleep_h - 6.5) * 1.0
        pred_score = max(5.0, min(25.0, pred_score))

        prediction = Prediction(
            assessment_id=assessment.id,
            student_id=student.id,
            model_version="v1.0",
            category=cat,
            probs=json.dumps({"low": round(1.0 - prob_high, 4), "high": round(prob_high, 4)}),
            score=round(pred_score, 2),
            created_at=assessment.created_at
        )
        db.add(prediction)
        db.flush()

        # Feedback
        agreement = random.choices(["Yes", "No", "Not sure"], weights=[0.75, 0.15, 0.10])[0]
        feedback = StudentFeedback(
            prediction_id=prediction.id,
            student_id=student.id,
            agreement=agreement,
            score_feels_right=agreement,
            comment="Demo generated feedback entry" if random.random() > 0.6 else None,
            is_demo=True,
            created_at=assessment.created_at + datetime.timedelta(minutes=5)
        )
        db.add(feedback)

        # Outcome (bo1..bo5)
        # Correlated with features with realistic noise
        base_item = 2 if cat == "Low Risk" else 4
        bo1 = max(1, min(5, base_item + random.choice([-1, 0, 1])))
        bo2 = max(1, min(5, base_item + random.choice([-1, 0, 1])))
        bo3 = max(1, min(5, base_item + random.choice([-1, 0, 1])))
        bo4 = max(1, min(5, base_item + random.choice([-1, 0, 1])))
        bo5 = max(1, min(5, base_item + random.choice([-1, 0, 1])))
        measured_score = float(bo1 + bo2 + bo3 + bo4 + bo5)
        measured_cat = "High Risk" if measured_score >= 15.0 else "Low Risk"

        outcome = VerifiedOutcome(
            student_id=student.id,
            assessment_id=assessment.id,
            bo1=bo1,
            bo2=bo2,
            bo3=bo3,
            bo4=bo4,
            bo5=bo5,
            measured_score=measured_score,
            measured_category=measured_cat,
            days_after_assessment=float(random.randint(2, 14)),
            is_demo=True,
            created_at=assessment.created_at + datetime.timedelta(days=random.randint(2, 14))
        )
        db.add(outcome)
        created_students += 1

    db.commit()
    return {
        "status": "success",
        "message": f"Successfully seeded {created_students} demo records (is_demo=True).",
        "seeded_count": created_students
    }
