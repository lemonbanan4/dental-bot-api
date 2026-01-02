from fastapi import APIRouter, HTTPException, Header, Request
from app.config import settings
from app.supabase_db import get_supabase_client
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


@router.get('/ui')
def admin_ui(request: Request, x_api_key: str = Header(default="")):
        # Small admin UI for onboarding clinics — requires API key for actions, but the page can be served publicly for convenience.
        html = '''
        <!doctype html>
        <html>
        <head><meta charset="utf-8"><title>Admin — Onboard Clinic</title>
        <style>body{font-family:system-ui,Arial,sans-serif;padding:20px}label{display:block;margin-top:8px}input,textarea{width:100%;padding:8px;border:1px solid #ddd;border-radius:6px}</style>
        </head>
        <body>
            <h2>Onboard Clinic</h2>
            <div>
                <label>API Key (admin): <input id="apiKey" type="password" placeholder="x-api-key" /></label>
                <label>Clinic ID: <input id="clinicId" /></label>
                <label>Clinic name: <input id="clinicName" /></label>
                <label>Contact email: <input id="contactEmail" /></label>
                <label>Booking URL: <input id="bookingUrl" /></label>
                <label>Logo URL: <input id="logoUrl" /></label>
                <label>Preview text: <input id="previewText" /></label>
                <label>Additional data (JSON): <textarea id="extra" rows=4 placeholder='{"plan":"pro"}'></textarea></label>
                <div style="margin-top:12px"><button id="saveBtn">Save & Send Onboarding</button></div>
                <pre id="out" style="margin-top:12px;background:#f8fafc;padding:12px;border-radius:6px;border:1px solid #eef"></pre>
            </div>
            <script>
                async function upsert(){
                    const apiKey = document.getElementById('apiKey').value.trim();
                    const clinicId = document.getElementById('clinicId').value.trim();
                    const payload = {
                        clinic_id: clinicId,
                        clinic_name: document.getElementById('clinicName').value.trim(),
                        contact_email: document.getElementById('contactEmail').value.trim(),
                        booking_url: document.getElementById('bookingUrl').value.trim(),
                        logo_url: document.getElementById('logoUrl').value.trim(),
                        preview_text: document.getElementById('previewText').value.trim()
                    };
                    try { Object.assign(payload, JSON.parse(document.getElementById('extra').value || '{}')); } catch(e){}
                    const res = await fetch('/admin/clinics', { method: 'PUT', headers: { 'Content-Type':'application/json', 'x-api-key': apiKey }, body: JSON.stringify(payload) });
                    const data = await res.json().catch(()=>({status:res.status}));
                    document.getElementById('out').textContent = JSON.stringify(data, null, 2);
                }
                document.getElementById('saveBtn').onclick = upsert;
            </script>
        </body></html>
        '''
        return html

