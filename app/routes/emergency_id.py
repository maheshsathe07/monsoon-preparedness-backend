import json
from uuid import uuid4

from fastapi import APIRouter

from app.models.schemas import EmergencyIdRequest, EmergencyIdResponse
from app.services.supabase_service import supabase
from app.utils.pdf_generator import generate_emergency_id_pdf
from app.utils.qr_generator import generate_qr

router = APIRouter(prefix="/emergency-id", tags=["emergency-id"])


@router.post("", response_model=EmergencyIdResponse)
async def create_emergency_id(request: EmergencyIdRequest) -> EmergencyIdResponse:
    emergency_id = f"eid_{uuid4().hex[:12]}"
    public_url = f"/api/v1/emergency-id/{emergency_id}"
    payload = request.model_dump(mode="json")
    qr_path = generate_qr(json.dumps({"id": emergency_id, "url": public_url}), emergency_id)
    lines = [
        f"Name: {request.full_name}",
        f"DOB: {request.dob or 'Not provided'}",
        f"Blood group: {request.blood_group or 'Not provided'}",
        f"Allergies: {', '.join(request.allergies) or 'None listed'}",
        f"Medicines: {', '.join(request.meds) or 'None listed'}",
        f"Insurance: {request.insurance_details or 'Not provided'}",
    ]
    for contact in request.emergency_contacts:
        lines.append(f"Contact: {contact.name} {contact.phone} {contact.relation or ''}".strip())
    pdf_path = generate_emergency_id_pdf(request.full_name, qr_path, lines, emergency_id)
    await supabase.insert(
        "emergency_ids",
        {
            "id": emergency_id,
            "user_id": request.user_id,
            "qr_code_url": qr_path,
            "pdf_url": pdf_path,
            "encrypted_data": payload,
            "created_at": supabase.now(),
        },
    )
    return EmergencyIdResponse(id=emergency_id, public_url=public_url, qr_code_path=qr_path, pdf_path=pdf_path)


@router.get("/{emergency_id}")
async def get_emergency_id(emergency_id: str) -> dict:
    rows = await supabase.select("emergency_ids", {"id": emergency_id}, limit=1)
    return rows[0]["encrypted_data"] if rows else {"detail": "Emergency ID not found"}
