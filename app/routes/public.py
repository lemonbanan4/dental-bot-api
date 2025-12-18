from fastapi import APIRouter, HTTPException
from app.supabase_db import get_clinic_by_public_id

router = APIRouter(prefix="/public", tags=["public"])

@router.get("/clinic/{clinic_id}")
def public_clinic(clinic_id: str):
    clinic = get_clinic_by_public_id(clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    
    # return only safe public fields
    return {
        "clinic_id": clinic["clinic_id"],
        "clinic_name": clinic["clinic_name"],
        "booking_url": clinic["booking_url"],
        "contact_phone": clinic["contact_phone"],
        "contact_email": clinic["contact_email"],
        "opening_hours": clinic["opening_hours"],
        "location": clinic["location"],
    }

