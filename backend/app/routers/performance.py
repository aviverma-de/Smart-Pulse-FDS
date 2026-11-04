"""
SmartPulse Model Performance Router
"""

from fastapi import APIRouter
from ..model_loader import container

router = APIRouter(prefix="/api/model", tags=["performance"])

@router.get("/performance")
async def get_performance():
    return container.model_performance
