"""
SmartPulse Statistical Insights Router
"""

from fastapi import APIRouter
from ..model_loader import container

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("/insights")
async def get_insights():
    return {
        "tests": container.hypothesis_tests,
        "n_students": container.overview_stats.get("n_students", 132),
        "alpha": 0.05,
        "significant_count": container.overview_stats.get("significant_tests_count", 2)
    }
