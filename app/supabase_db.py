from __future__ import annotations

from typing import Optional
from supabase import Client, create_client
from app.config import settings


# Lazy-init supabase client so imports don't crash when env vars are missing.
_sb: Optional[Client] = None


def get_supabase_client() -> Client:
    """Return a Supabase Client, initializing it on first use.

    Raises a clear RuntimeError if the required env vars are not configured
    or the client cannot be created. This avoids failing at import time.
    """
    global _sb
    if _sb is not None:
        return _sb

    supabase_url = settings.supabase_url.strip()
    supabase_key = settings.supabase_service_role_key.strip()

    if not supabase_url or not supabase_key:
        raise RuntimeError("Supabase URL/service role key are not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")

    try:
        _sb = create_client(supabase_url, supabase_key)
    except Exception as exc:  # surface clear error if the key is wrong
        raise RuntimeError("Failed to create Supabase client (check SUPABASE_SERVICE_ROLE_KEY)") from exc

    return _sb


def get_clinic_by_public_id(public_clinic_id: str) -> Optional[dict]:
    sb = get_supabase_client()
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
        user_locale: Optional[str],
        page_url: Optional[str],
        user_agent: Optional[str],
        ip_hash: Optional[str],
) -> dict:
    sb = get_supabase_client()
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
    sb = get_supabase_client()
    sb.table("chat_messages").insert({
        "session_id": session_uuid,
        "role": role,
        "content": content,
    }).execute()

def fetch_recent_messages(session_uuid: str, limit: int = 10) -> list[dict]:
    sb = get_supabase_client()
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
        session_uuid: Optional[str],
        name: Optional[str],
        phone: Optional[str],
        email: Optional[str],
        message: Optional[str],
) -> dict:
    sb = get_supabase_client()
    res = sb.table("leads").insert({
        "clinic_id": clinic_uuid,
        "session_id": session_uuid,
        "name": name,
        "phone": phone,
        "email": email,
        "message": message,
    }).execute()
    return (res.data or [])[0] if res.data else {"ok": True}

def log_competitor_query(
    clinic_uuid: str,
    session_uuid: str,
    query: str,
    detected_keyword: str
) -> None:
    sb = get_supabase_client()
    sb.table("competitor_queries").insert({
        "clinic_id": clinic_uuid,
        "session_id": session_uuid,
        "query": query,
        "detected_keyword": detected_keyword,
    }).execute()

def delete_session_messages(session_uuid: str) -> None:
    sb = get_supabase_client()
    sb.table("chat_messages").delete().eq("session_id", session_uuid).execute()

def get_competitor_queries(limit: int = 50) -> list[dict]:
    sb = get_supabase_client()
    res = (
        sb.table("competitor_queries")
        .select("*, clinics(clinic_name, clinic_id)")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []

def insert_feedback(clinic_uuid: str, session_uuid: str, rating: str, comment: Optional[str]) -> None:
    sb = get_supabase_client()
    sb.table("chat_feedback").insert({
        "clinic_id": clinic_uuid,
        "session_id": session_uuid,
        "rating": rating,
        "comment": comment,
    }).execute()

def get_feedback_stats(limit: int = 100) -> list[dict]:
    sb = get_supabase_client()
    res = (
        sb.table("chat_feedback")
        .select("*, clinics(clinic_name, clinic_id)")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []

def get_feedback_counts() -> list[dict]:
    sb = get_supabase_client()
    # Fetch data to aggregate
    # Note: For very large datasets, consider creating a SQL View or RPC.
    res = (
        sb.table("chat_feedback")
        .select("rating, clinic_id, clinics(clinic_name)")
        .limit(1000)
        .execute()
    )
    rows = res.data or []
    
    stats = {}
    for row in rows:
        c_id = row.get("clinic_id")
        if not c_id:
            continue
            
        if c_id not in stats:
            c_name = row.get("clinics", {}).get("clinic_name", "Unknown") if row.get("clinics") else "Unknown"
            stats[c_id] = {"clinic_id": c_id, "clinic_name": c_name, "up": 0, "down": 0, "total": 0}
        
        rating = row.get("rating")
        if rating == "up":
            stats[c_id]["up"] += 1
        elif rating == "down":
            stats[c_id]["down"] += 1
        stats[c_id]["total"] += 1
        
    return list(stats.values())
