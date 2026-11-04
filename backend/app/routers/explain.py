"""
SmartPulse Explainability Router
"""

from fastapi import APIRouter
from ..models import AssessmentInput, ExplainResponse
from ..services.prediction_service import explain_prediction

router = APIRouter(prefix="/api", tags=["explain"])

@router.post("/explain", response_model=ExplainResponse)
async def api_explain(payload: AssessmentInput):
    return explain_prediction(payload)
