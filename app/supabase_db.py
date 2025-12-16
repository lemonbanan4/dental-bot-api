from __future__ import annotations

from typing import Optional
from supabase import Client, create_client
from app.config import settings
import os
print("SUPABASE_URL:", os.getenv("SUPABASE_URL"))
print("SUPABASE_SERVICE_ROLE_KEY present:", bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY")))


# Normalize values to avoid trailing newlines/spaces from env files.
supabase_url = settings.supabase_url.strip()
supabase_key = settings.supabase_service_role_key.strip()

# Initialize client once. Fail fast if creds are missing.
if not supabase_url or not supabase_key:
    raise RuntimeError("Supabase URL/service role key are not configured")

try:
    sb: Client = create_client(supabase_url, supabase_key)
except Exception as exc:  # surface clear error if the key is wrong
    raise RuntimeError("Failed to create Supabase client (check SUPABASE_SERVICE_ROLE_KEY)") from exc


def get_clinic_by_public_id(public_clinic_id: str) -> Optional[dict]:
    res = (
        sb.table("clinics")
        .select("*")
        .eq("clinic_id", public_clinic_id)
        .limit(1)
        .execute()
    )
    data = res.data or []
    return data[0] if data else None

def get_or_create_session(
        clinic_uuid: str,
        session_key: str,
        user_locale: str | None,
        page_url: str | None,
        user_agent: str | None,
        ip_hash: str | None,
) -> dict:
    # Try fetch
    res = sb.table("chat_sessions").select("*").eq("session_key", session_key).limit(1).execute()
    rows = res.data or []
    if rows:
        return rows[0]
    
    # Create
    payload = {
        "clinic_id": clinic_uuid,
        "session_key": session_key,
        "user_locale": user_locale,
        "page_url": page_url,
        "user_agent": user_agent,
        "ip_hash": ip_hash,
    }
    created = sb.table("chat_sessions").insert(payload).execute()
    return (created.data or [payload])[0]

def insert_message(session_uuid: str, role: str, content: str) -> None:
    sb.table("chat_messages").insert({
        "session_id": session_uuid,
        "role": role,
        "content": content,
    }).execute()

def fetch_recent_messages(session_uuid: str, limit: int = 10) -> list[dict]:
    # newest first -> reverse for chronological order
    res = (
        sb.table("chat_messages")
        .select("role,content,created_at")
        .eq("session_id", session_uuid)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = res.data or []
    rows.reverse()
    return [{"role": r["role"], "content": r["content"]} for r in rows]
    
def create_lead(
        clinic_uuid: str,
        session_uuid: str | None,
        name: str | None,
        phone: str | None,
        email: str | None,
        message: str | None,
) -> dict:
    res = sb.table("leads").insert({
        "clinic_id": clinic_uuid,
        "session_id": session_uuid,
        "name": name,
        "phone": phone,
        "email": email,
        "message": message,
    }).execute()
    return (res.data or [])[0] if res.data else {"ok": True}


