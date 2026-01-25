from fastapi import APIRouter, HTTPException, Header, Request
from typing import Optional
from fastapi.responses import RedirectResponse
from app.config import settings
from app.supabase_db import get_supabase_client, get_competitor_queries, get_feedback_stats, get_feedback_counts
from app.utils.email import send_onboarding_email

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
        # send onboarding email (async trigger not required here)
        contact_email = payload.get('contact_email') or payload.get('email')
        if contact_email:
            try:
                send_onboarding_email(contact_email, payload.get('clinic_name'), snippet, payload.get('logo_url'), payload.get('preview_text'))
            except Exception:
                pass

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

@router.get("/competitor-queries")
def list_competitor_queries(limit: int = 50, x_api_key: str = Header(default="")):
    require_api_key(x_api_key)
    return {"queries": get_competitor_queries(limit)}

@router.get("/feedback-stats")
def list_feedback_stats(limit: int = 100, x_api_key: str = Header(default="")):
    require_api_key(x_api_key)
    return {"feedback": get_feedback_stats(limit)}

@router.get("/feedback-counts")
def list_feedback_counts(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    x_api_key: str = Header(default="")
):
    require_api_key(x_api_key)
    return {"counts": get_feedback_counts(start_date, end_date)}


@router.get('/ui')
def admin_ui(request: Request, x_api_key: str = Header(default="")):
        # Serve the static admin UI for onboarding clinics
        return RedirectResponse(url='/static/admin.html')
