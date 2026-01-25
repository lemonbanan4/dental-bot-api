from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import json
from uuid import uuid4
import time

from app.models import ChatRequest, ChatResponse
from app.prompts import get_system_prompt
from app.services.llm import chat_completion, chat_completion_stream
from app.services.guardrails import is_emergency, is_symptom_or_diagnosis_request
from app.utils.rate_limit import limit
from app.utils.privacy import hash_ip
from app.config import settings
from app.supabase_db import (
    get_clinic_by_public_id,
    get_or_create_session,
    insert_message,
    fetch_recent_messages,
    log_competitor_query,
)

router = APIRouter(prefix="/chat", tags=["chat"])

def run_with_retry(func, *args, **kwargs):
    """Executes a function with retries for background tasks."""
    max_retries = 3
    delay = 1
    
    for i in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if i == max_retries - 1:
                print(f"Background task failed after {max_retries} attempts: {e}")
                return
            time.sleep(delay)
            delay *= 2

# Fallback clinic data for demo/testing
DEMO_CLINICS = {
    "lemon-main": {
        "id": "demo-lemon-main",
        "clinic_id": "lemon-main",
        "clinic_name": "Lemon Techno",
        "location": "Demo Location",
        "opening_hours": "9 AM - 6 PM",
        "services": ["Consultation", "AI Support"],
        "insurance": ["All"],
        "price_ranges": {"consultation": "Free"},
        "languages": ["English"],
        "booking_url": "https://calendly.com/lemon-techno/demo",
        "emergency_instructions": "Contact us immediately at +1-800-LEMON",
        "contact_phone": "+1-800-LEMON",
        "contact_email": "support@lemon-techno.org",
    },
    "dental-demo": {
        "id": "demo-dental",
        "clinic_id": "dental-demo",
        "clinic_name": "Dental Demo",
        "location": "Demo Location",
        "opening_hours": "9 AM - 6 PM",
        "services": ["Consultation", "AI Support"],
        "insurance": ["All"],
        "price_ranges": {"consultation": "Free"},
        "languages": ["English"],
        "booking_url": "https://demo.dental",
        "emergency_instructions": "Contact us immediately",
        "contact_phone": "+1-800-DEMO",
        "contact_email": "support@demo.dental",
    },
    "beauty-demo": {
        "id": "demo-beauty",
        "clinic_id": "beauty-demo",
        "clinic_name": "Beauty Demo",
        "location": "Demo Location",
        "opening_hours": "9 AM - 6 PM",
        "services": ["Consultation", "AI Support"],
        "insurance": ["All"],
        "price_ranges": {"consultation": "Free"},
        "languages": ["English"],
        "booking_url": "https://demo.beauty",
        "emergency_instructions": "Contact us immediately",
        "contact_phone": "+1-800-DEMO",
        "contact_email": "support@demo.beauty",
    },
    "realestate-demo": {
        "id": "demo-realestate",
        "clinic_id": "realestate-demo",
        "clinic_name": "Real Estate Demo",
        "location": "Demo Location",
        "opening_hours": "9 AM - 6 PM",
        "services": ["Consultation", "AI Support"],
        "insurance": ["All"],
        "price_ranges": {"consultation": "Free"},
        "languages": ["English"],
        "booking_url": "https://demo.realestate",
        "emergency_instructions": "Contact us immediately",
        "contact_phone": "+1-800-DEMO",
        "contact_email": "support@demo.realestate",
    },
    "retail-demo": {
        "id": "demo-retail",
        "clinic_id": "retail-demo",
        "clinic_name": "Retail Demo",
        "location": "Demo Location",
        "opening_hours": "9 AM - 6 PM",
        "services": ["Consultation", "AI Support"],
        "insurance": ["All"],
        "price_ranges": {"consultation": "Free"},
        "languages": ["English"],
        "booking_url": "https://demo.retail",
        "emergency_instructions": "Contact us immediately",
        "contact_phone": "+1-800-DEMO",
        "contact_email": "support@demo.retail",
    },
    "support-demo": {
        "id": "demo-support",
        "clinic_id": "support-demo",
        "clinic_name": "Support Demo",
        "location": "Demo Location",
        "opening_hours": "9 AM - 6 PM",
        "services": ["Consultation", "AI Support"],
        "insurance": ["All"],
        "price_ranges": {"consultation": "Free"},
        "languages": ["English"],
        "booking_url": "https://demo.support",
        "emergency_instructions": "Contact us immediately",
        "contact_phone": "+1-800-DEMO",
        "contact_email": "support@demo.support",
    },
    "smile-city-001": {
        "id": "demo-smile-city",
        "clinic_id": "smile-city-001",
        "clinic_name": "Smile City Dental",
        "location": "123 Main St",
        "opening_hours": "9 AM - 6 PM",
        "services": ["Cleaning", "Whitening", "Implants"],
        "insurance": ["Dental Plus", "SmileCare"],
        "price_ranges": {"cleaning": "$100-150", "whitening": "$200-400"},
        "languages": ["English", "Spanish"],
        "booking_url": "https://booking.smile-city.com",
        "emergency_instructions": "Call emergency line: 911",
        "contact_phone": "+1-555-SMILE",
        "contact_email": "hello@smile-city.com",
    },
}

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request, background_tasks: BackgroundTasks, stream: bool = False):
    limit(request, max_per_minute=90)

    # Try Supabase first, then fallback to demo data
    clinic = None
    try:
        clinic = get_clinic_by_public_id(req.clinic_id)
    except Exception as e:
        # Supabase not configured or connection failed - use demo data
        print(f"Supabase lookup failed: {e}")
    
    # If not in Supabase, try demo clinics (for backward compatibility)
    if not clinic and req.clinic_id in DEMO_CLINICS:
        clinic = DEMO_CLINICS[req.clinic_id]
    
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    system = get_system_prompt(clinic)

    # --- DEBUG LOGGING ---
    print(f"[CHAT_DEBUG] Clinic ID: {req.clinic_id}, Clinic Name: {clinic.get('clinic_name')}")
    print(f"[CHAT_DEBUG] Generated System Prompt: {system[:300]}...") # Log first 300 chars
    # ---------------------

    session_id = req.session_id or str(uuid4())

    user_text = req.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Empty message")

    # Create/find session (log basic metadata)
    ip = request.client.host if request.client else None
    ip_h = hash_ip(ip, settings.ip_hash_salt)
    page_url = (req.metadata or {}).get("page_url") if req.metadata else None
    user_agent = request.headers.get("user-agent")

    # Determine if this is a real clinic (using Supabase) or a demo clinic (in-memory)
    clinic_db_id = clinic.get("id")
    is_real_clinic = False
    if clinic_db_id and isinstance(clinic_db_id, str) and not clinic_db_id.startswith("demo-"):
        is_real_clinic = True

    # Try to use Supabase session management if clinic is in database
    if is_real_clinic and isinstance(clinic_db_id, str):
        try:
            session = get_or_create_session(
                clinic_uuid=clinic_db_id,
                session_key=session_id,
                user_locale=req.locale_hint,
                page_url=page_url,
                user_agent=user_agent,
                ip_hash=ip_h,
            )
        except Exception as e:
            # Fallback if Supabase fails
            print(f"Warning: Supabase session creation failed: {e}. Using in-memory fallback.")
            session = {"id": session_id, "session_key": session_id}
    else:
        # For demo clinics, use in-memory session
        session = {"id": session_id, "session_key": session_id}

    # Try to log message to Supabase if clinic is in database
    if is_real_clinic:
        # Log user message in background
        background_tasks.add_task(run_with_retry, insert_message, session["id"], "user", user_text)

    # --- GUARDRAILS (Medical Only) ---
    # Determine if this is a medical context to avoid triggering medical warnings for retail/real estate
    name_lower = clinic.get("clinic_name", "").lower()
    is_medical_context = any(x in name_lower for x in ['dental', 'smile', 'ortho', 'tooth', 'dentist', 'medical', 'doctor', 'clinic', 'beauty', 'aesthetic', 'skin', 'derma'])

    if is_medical_context:
        if is_emergency(user_text):
            reply = (
                f"{clinic.get('emergency_instructions')}\n\n"
                f"If you cannot reach the clinic quickly, seek urgent medical care.\n\n"
                f"This assistant provides general information and does not replace professional medical advice."
            )
            if is_real_clinic:
                background_tasks.add_task(run_with_retry, insert_message, session["id"], "assistant", reply)
            return ChatResponse(reply=reply, session_id=session_id, handoff=True, handoff_reason="emergency")

        if is_symptom_or_diagnosis_request(user_text):
            reply = (
                f"I can't provide medical advice or diagnose symptoms. "
                f"The safest step is to book an appointment so a clinician can assess you.\n\n"
                f"You can book here: {clinic.get('booking_url')}\n"
                f"Or contact the clinic: {clinic.get('contact_phone')} / {clinic.get('contact_email')}\n\n"
                f"This assistant provides general information and does not replace professional medical advice."
            )
            if is_real_clinic:
                background_tasks.add_task(run_with_retry, insert_message, session["id"], "assistant", reply)
            return ChatResponse(reply=reply, session_id=session_id, handoff=True, handoff_reason="medical_advice_request")

    # --- GUARDRAILS (Competitors) ---
    # Prevent discussion of competitors.
    competitor_keywords = ["competitor", "other clinic", "other dentist", "other agency", "compare you to"]
    matched_keyword = next((x for x in competitor_keywords if x in user_text.lower()), None)

    if matched_keyword:
        reply = (
            f"I can only provide information about {clinic.get('clinic_name')}. "
            f"If you have questions about our services, prices, or availability, feel free to ask!"
        )
        if is_real_clinic:
            background_tasks.add_task(run_with_retry, insert_message, session["id"], "assistant", reply)
            background_tasks.add_task(run_with_retry, log_competitor_query, clinic.get("id"), session["id"], user_text, matched_keyword)
        return ChatResponse(reply=reply, session_id=session_id, handoff=False)

    # ✅ memory: last N messages
    if is_real_clinic:
        try:
            history = fetch_recent_messages(session["id"], limit=settings.chat_memory_messages)
            llm_messages = [m for m in history if m["role"] in ("user", "assistant")]
        except Exception as e:
            # Fallback if Supabase fails
            print(f"Warning: Supabase fetch failed: {e}")
            llm_messages = [{"role": "user", "content": user_text}]
    else:
        # For demo clinics, just use current message
        llm_messages = [{"role": "user", "content": user_text}]

    if not stream:
        try:
            llm_reply = await chat_completion(system=system, messages=llm_messages)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LLM error: {str(e)}")

        # ✅ log assistant message
        if is_real_clinic:
            background_tasks.add_task(run_with_retry, insert_message, session["id"], "assistant", llm_reply)

        return ChatResponse(reply=llm_reply, session_id=session_id, handoff=False)

    # Streaming path (NDJSON lines). Each yielded line is a JSON object.
    async def event_stream():
        parts = []
        try:
            async for chunk in chat_completion_stream(system=system, messages=llm_messages):
                parts.append(chunk)
                obj = {"text": chunk}
                yield (json.dumps(obj) + "\n").encode()

            full = "".join(parts)
            # log the finished assistant message
            if is_real_clinic:
                background_tasks.add_task(run_with_retry, insert_message, session["id"], "assistant", full)

            # final metadata line
            meta: Dict[str, Any] = {"done": True}
            if clinic.get("booking_url"):
                meta["booking_url"] = clinic.get("booking_url")
            yield (json.dumps(meta) + "\n").encode()
        except Exception as e:
            # send an error line for the client to consume
            yield (json.dumps({"error": str(e)}) + "\n").encode()

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")

@router.get("/history")
async def get_history(clinic_id: str, session_id: str):
    """Retrieve chat history for a specific session."""
    # Try Supabase first
    clinic = None
    try:
        clinic = get_clinic_by_public_id(clinic_id)
    except Exception:
        pass
    
    # If not found in DB, check demo clinics
    if not clinic:
        if clinic_id in DEMO_CLINICS:
            # Demo clinics are stateless/in-memory per request in this architecture
            return {"history": []}
        raise HTTPException(status_code=404, detail="Clinic not found")

    # Real clinic: fetch from Supabase
    try:
        # Resolve session_key to internal session_id
        session = get_or_create_session(
            clinic_uuid=clinic["id"],
            session_key=session_id,
            user_locale=None,
            page_url=None,
            user_agent=None,
            ip_hash=None,
        )
        messages = fetch_recent_messages(session["id"], limit=50)
        return {"history": messages}
    except Exception as e:
        print(f"Error fetching history: {e}")
        return {"history": []}
