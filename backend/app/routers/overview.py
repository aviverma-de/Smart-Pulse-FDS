"""
SmartPulse Overview Router
"""

from fastapi import APIRouter
from ..model_loader import container

router = APIRouter(prefix="/api", tags=["overview"])

@router.get("/overview")
async def get_overview():
    return container.overview_stats
