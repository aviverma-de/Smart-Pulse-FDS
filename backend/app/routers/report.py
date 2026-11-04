"""
SmartPulse PDF Report Router
"""

from fastapi import APIRouter, Response
from ..models import ReportRequest
from ..services.report_service import generate_pdf_report

router = APIRouter(prefix="/api", tags=["report"])

@router.post("/report")
async def api_generate_report(payload: ReportRequest):
    pdf_bytes = generate_pdf_report(payload)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="SmartPulse_Wellness_Report.pdf"'
        }
    )
