"""
SmartPulse Prediction Routers
"""

from fastapi import APIRouter
from ..models import AssessmentInput, PredictionResponse, ScoreResponse
from ..services.prediction_service import predict_category, predict_score

router = APIRouter(prefix="/api/predict", tags=["prediction"])

@router.post("/category", response_model=PredictionResponse)
async def api_predict_category(payload: AssessmentInput):
    return predict_category(payload)

@router.post("/score", response_model=ScoreResponse)
async def api_predict_score(payload: AssessmentInput):
    return predict_score(payload)
