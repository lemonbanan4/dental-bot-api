from fastapi import APIRouter, HTTPException, Request
from uuid import uuid4

from app.models import ChatRequest, ChatResponse
from app.prompts import BASE_SYSTEM, clinic_context_block
from app.services.llm import chat_completion
from app.services.guardrails import is_emergency, is_symptom_or_diagnosis_request
from app.utils.rate_limit import limit
from app.utils.privacy import hash_ip
from app.config import settings
from app.supabase_db import (
    get_clinic_by_public_id,
    get_or_create_session,
    insert_message,
    fetch_recent_messages,
)

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    limit(request, max_per_minute=90)

    # ✅ Supabase clinic lookup (not app.db)
    clinic = get_clinic_by_public_id(req.clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    session_id = req.session_id or str(uuid4())

    user_text = req.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Empty message")

    # Create/find session (log basic metadata)
    ip = request.client.host if request.client else None
    ip_h = hash_ip(ip, settings.ip_hash_salt)
    page_url = (req.metadata or {}).get("page_url") if req.metadata else None
    user_agent = request.headers.get("user-agent")

    session = get_or_create_session(
        clinic_uuid=clinic["id"],   # internal UUID
        session_key=session_id,
        user_locale=req.locale_hint,
        page_url=page_url,
        user_agent=user_agent,
        ip_hash=ip_h,
    )

    # ✅ log user message
    insert_message(session["id"], "user", user_text)

    # Guardrails
    if is_emergency(user_text):
        reply = (
            f"{clinic.get('emergency_instructions')}\n\n"
            f"If you cannot reach the clinic quickly, seek urgent medical care.\n\n"
            f"This assistant provides general information and does not replace professional medical advice."
        )
        insert_message(session["id"], "assistant", reply)
        return ChatResponse(reply=reply, session_id=session_id, handoff=True, handoff_reason="emergency")

    if is_symptom_or_diagnosis_request(user_text):
        reply = (
            f"I can't provide medical advice or diagnose symptoms. "
            f"The safest step is to book an appointment so a clinician can assess you.\n\n"
            f"You can book here: {clinic.get('booking_url')}\n"
            f"Or contact the clinic: {clinic.get('contact_phone')} / {clinic.get('contact_email')}\n\n"
            f"This assistant provides general information and does not replace professional medical advice."
        )
        insert_message(session["id"], "assistant", reply)
        return ChatResponse(reply=reply, session_id=session_id, handoff=True, handoff_reason="medical_advice_request")

    # ✅ memory: last N messages
    history = fetch_recent_messages(session["id"], limit=settings.chat_memory_messages)
    llm_messages = [m for m in history if m["role"] in ("user", "assistant")]

    system = BASE_SYSTEM + "\n\n" + clinic_context_block(clinic)

    try:
        llm_reply = await chat_completion(system=system, messages=llm_messages)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {str(e)}")

    # ✅ log assistant message
    insert_message(session["id"], "assistant", llm_reply)

    return ChatResponse(reply=llm_reply, session_id=session_id, handoff=False)
