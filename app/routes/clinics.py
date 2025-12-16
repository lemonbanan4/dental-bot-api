from fastapi import APIRouter, Depends, HTTPException
from app.security import require_api_key
from app.models import ClinicUpsertRequest, ClinicProfile
from app.db import get_clinic, upsert_clinic

router = APIRouter(prefix="/clinics", tags=["clinics"])


@router.post("", response_model=dict)
def create_or_update_clinic(profile: ClinicProfile):
    return upsert_clinic(profile)

@router.get("/{clinic_id}", dependencies=[Depends(require_api_key)])
def read_clinic(clinic_id: str):
    clinic = get_clinic(clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic
@router.get("/debug/ids")
def list_ids():
    from app.db import CLINICS
    return {"clinics_ids": list(CLINICS.keys())}

@router.put("", dependencies=[Depends(require_api_key)])
def put_clinic(profile: ClinicUpsertRequest):
    clinic = upsert_clinic(profile)
    return {"ok": True, "clinic": clinic}


