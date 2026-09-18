from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.models.user import User
from app.services.pdf_report import generate_report_pdf

router = APIRouter(prefix="/reports", tags=["reports"])

class ReportRequest(BaseModel):
    title: str
    markdown_content: str

@router.post("/generate")
async def generate_report(
    req: ReportRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate a PDF report from markdown content."""
    try:
        pdf_bytes = generate_report_pdf(req.title, req.markdown_content)
        return StreamingResponse(
            pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=\"{req.title.replace(' ', '_')}.pdf\""
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
