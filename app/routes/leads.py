from fastapi import APIRouter, HTTPException, Depends
from app.models import LeadRequest, LeadResponse
from app.supabase_db import get_clinic_by_public_id, create_lead, get_or_create_session
from app.rate_limit import limit_leads

# Primary router kept for backwards compatibility (/lead)
router = APIRouter(prefix="/lead", tags=["lead"])

# Alias router to accept requests at /leads as well (some embeds post to /leads)
router2 = APIRouter(prefix="/leads", tags=["lead"])


def _handle_lead(req: LeadRequest):
    clinic = get_clinic_by_public_id(req.clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    session_uuid = None
    if req.session_id:
        # Ensure session exists (minimal create; no metadata here)
        sess = get_or_create_session(
            clinic_uuid=clinic["id"],
            session_key=req.session_id,
            user_locale=None,
            page_url=None,
            user_agent=None,
            ip_hash=None,
        )
        session_uuid = sess["id"]

    create_lead(
        clinic_uuid=clinic["id"],
        session_uuid=session_uuid,
        name=req.name,
        phone=req.phone,
        email=req.email,
        message=req.message,
    )
    return LeadResponse(ok=True)


@router.post("", response_model=LeadResponse)
def lead(req: LeadRequest, _rl=Depends(limit_leads())):
    return _handle_lead(req)


@router2.post("", response_model=LeadResponse)
def lead_alias(req: LeadRequest, _rl=Depends(limit_leads())):
    return _handle_lead(req)
