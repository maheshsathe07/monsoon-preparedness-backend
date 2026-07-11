from uuid import uuid4

from fastapi import APIRouter

from app.models.schemas import RecoveryReportRequest, RecoveryReportResponse
from app.services.openai_service import openai_service
from app.services.supabase_service import supabase
from app.utils.pdf_generator import generate_report_pdf

router = APIRouter(prefix="/generate-report", tags=["recovery-reports"])


@router.post("", response_model=RecoveryReportResponse)
async def generate_report(request: RecoveryReportRequest) -> RecoveryReportResponse:
    report_id = f"report_{uuid4().hex[:12]}"
    pdf_path = generate_report_pdf(
        "Monsoon Damage Report",
        [
            f"Incident date: {request.incident_date}",
            f"Insurance provider: {request.insurance_provider or 'Not provided'}",
            f"Damage description: {request.damage_description}",
            f"Photos: {', '.join(request.photos) or 'None'}",
        ],
        report_id,
    )
    result = await openai_service.recovery_report(request.model_dump(mode="json"), report_id, pdf_path)
    await supabase.insert(
        "recovery_reports",
        {
            "id": report_id,
            "user_id": request.user_id,
            "incident_date": request.incident_date,
            "damage_description": request.damage_description,
            "photos": request.photos,
            "insurance_provider": request.insurance_provider,
            "damage_category": result.damage_category,
            "severity_level": result.severity_level,
            "repair_estimate": result.repair_estimate,
            "incident_summary": result.incident_summary,
            "pdf_url": pdf_path,
            "created_at": supabase.now(),
        },
    )
    return result
