from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models import LeadRequest, LeadResponse
from app.supabase_db import get_clinic_by_public_id, create_lead, get_or_create_session
from app.rate_limit import limit_leads
from app.utils.email import send_lead_email
from app.config import settings

# Primary router kept for backwards compatibility (/lead)
router = APIRouter(prefix="/lead", tags=["lead"])

# Alias router to accept requests at /leads as well (some embeds post to /leads)
router2 = APIRouter(prefix="/leads", tags=["lead"])

# Fallback clinic data (same as in chat.py)
DEMO_CLINICS = {
    "lemon-main": {"id": "demo-lemon-main", "clinic_id": "lemon-main", "clinic_name": "Lemon Techno"},
    "smile-city-001": {"id": "demo-smile-city", "clinic_id": "smile-city-001", "clinic_name": "Smile City Dental"},
}

def _handle_lead(req: LeadRequest, bg: Optional[BackgroundTasks] = None):
    clinic = get_clinic_by_public_id(req.clinic_id)
    
    # Fallback to demo clinics if not found in Supabase
    if not clinic and req.clinic_id in DEMO_CLINICS:
        clinic = DEMO_CLINICS[req.clinic_id]
    
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    session_uuid = None
    if req.session_id and clinic.get("id") and not clinic.get("id").startswith("demo-"):
        # Only try Supabase session creation if it's a real clinic
        try:
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
        except Exception as e:
            # Fallback if Supabase fails
            print(f"Warning: Supabase session creation failed: {e}")
            session_uuid = None
    
    # Create lead in Supabase if it's a real clinic
    if clinic.get("id") and not clinic.get("id").startswith("demo-"):
        try:
            create_lead(
                clinic_uuid=clinic["id"],
                session_uuid=session_uuid,
                name=req.name,
                phone=req.phone,
                email=req.email,
                message=req.message,
            )
        except Exception as e:
            # Fallback if Supabase fails  
            print(f"Warning: Supabase create_lead failed: {e}")
    
    # Send notification email to clinic contact if configured
    clinic_email = clinic.get('contact_email') or clinic.get('email') or None
    if clinic_email and bg is not None:
        lead = {"name": req.name, "phone": req.phone, "email": req.email, "message": req.message, "session_id": req.session_id}
        # use background task to avoid slowing the API
        try:
            bg.add_task(send_lead_email, clinic_email, clinic.get('clinic_name') or req.clinic_id, lead)
        except Exception as e:
            # Fallback if email fails
            print(f"Warning: Email task failed: {e}")
    
    return LeadResponse(ok=True)


@router.post("", response_model=LeadResponse)
async def lead(req: LeadRequest, bg: BackgroundTasks):
    return _handle_lead(req, bg)


@router2.post("", response_model=LeadResponse)
async def lead_alias(req: LeadRequest, bg: BackgroundTasks):
    return _handle_lead(req, bg)

