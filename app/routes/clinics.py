from fastapi import APIRouter, Depends, HTTPException
from app.security import require_api_key
from app.models import ClinicProfile
from app.supabase_db import get_clinic_by_public_id, get_supabase_client

router = APIRouter(prefix="/clinics", tags=["clinics"])


@router.post("", response_model=dict)
def create_or_update_clinic(profile: ClinicProfile, _key=Depends(require_api_key)):
    """Create or update a clinic profile."""
    sb = get_supabase_client()
    res = sb.table("clinics").upsert(profile.model_dump(), on_conflict="clinic_id").execute()
    return {"ok": True, "clinic": (res.data or [profile.model_dump()])[0]}


@router.get("/{clinic_id}", dependencies=[Depends(require_api_key)])
def read_clinic(clinic_id: str):
    """Get clinic details."""
    clinic = get_clinic_by_public_id(clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic


@router.get("/debug/ids", dependencies=[Depends(require_api_key)])
def list_clinic_ids():
    """List all clinic IDs (debug endpoint)."""
    sb = get_supabase_client()
    res = sb.table("clinics").select("clinic_id, clinic_name").execute()
    return {"clinic_ids": [c["clinic_id"] for c in res.data or []]}



