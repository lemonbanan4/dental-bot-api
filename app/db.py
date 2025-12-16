from typing import Optional

from app.models import ClinicProfile

# In-memory store for MVP.
# Replace with real DB later.
CLINICS: dict[str, dict] = {}

def get_clinic(clinic_id: str) -> Optional[dict]:
    return CLINICS.get(clinic_id)

def upsert_clinic(profile: ClinicProfile) -> dict:
    CLINICS[profile.clinic_id] = profile.model_dump()
    return CLINICS[profile.clinic_id]
