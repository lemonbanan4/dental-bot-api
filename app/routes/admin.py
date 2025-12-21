from fastapi import APIRouter, HTTPException, Header
from app.config import settings
from app.supabase_db import get_supabase_client

router = APIRouter(prefix="/admin", tags=["admin"])

def require_api_key(x_api_key: str = Header(default="")):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
@router.put("/clinics")
def upsert_clinic(payload: dict, x_api_key: str = Header(default="")):
    require_api_key(x_api_key)

    clinic_id = (payload.get("clinic_id") or "").strip()
    if not clinic_id:
        raise HTTPException(status_code=400, detail="clinic_id is required")
    
    # Upsert by clinic_id
    sb = get_supabase_client()
    res = (
        sb.table("clinics")
        .upsert(payload, on_conflict="clinic_id")
        .execute()
    )
    

    api_base = (settings.public_api_base or "").rstrip("/")
    widget_src = (settings.public_widget_src or "").rstrip("/")

    if not api_base or not widget_src:
        snippet = None
    else:
        snippet = f"""<script
        src="{widget_src}"
        data-clinic="{clinic_id}"
        data-api="{api_base}"
        ></script>"""

        return {
            "ok": True,
            "clinic_id": clinic_id,
            "embed_snippet": snippet,
            "saved": res.data,
        }
    
@router.get("/clinics")
def list_clinics(x_api_key: str = Header(default="")):
    require_api_key(x_api_key)
    sb = get_supabase_client()
    res = sb.table("clinics").select("clinic_id,clinic_name,status,plan,created_at").order("created_at", desc=True).limit(100).execute()
    return {"clinics": res.data or []}

