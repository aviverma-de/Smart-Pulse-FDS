"""
SmartPulse What-If Simulator Router
"""

from fastapi import APIRouter
from ..models import WhatIfRequest, WhatIfResponse
from ..services.prediction_service import simulate_whatif

router = APIRouter(prefix="/api", tags=["whatif"])

@router.post("/whatif", response_model=WhatIfResponse)
async def api_whatif(payload: WhatIfRequest):
    return simulate_whatif(payload)
