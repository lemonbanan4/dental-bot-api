import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import copy
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS for your widget
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for chat history (for demo purposes)
CHAT_LOGS = {}
# In-memory storage for live sessions
LIVE_SESSIONS = {}
# In-memory storage for leads
LEADS = {}
# In-memory storage for typing status
SESSION_TYPING = {}
# In-memory storage for feedback stats
FEEDBACK_STATS = {}
# In-memory storage for maintenance mode
MAINTENANCE_MODE = {}
# In-memory storage for custom CSS
CUSTOM_CSS = {}
# In-memory storage for admin message queue
MESSAGE_QUEUE = {}
# In-memory storage for session metadata (IPs)
SESSION_METADATA = {}
# In-memory blocklist
BLOCKED_IPS = set()
# In-memory system logs
SYSTEM_LOGS = []

# Global Admin Key
ADMIN_KEY = "lemon-secret"

# --- DATA MODELS ---
class ChatRequest(BaseModel):
    clinic_id: str
    message: str
    session_id: str
    metadata: Optional[Dict[str, Any]] = None

class LeadRequest(BaseModel):
    clinic_id: str
    session_id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = None

class PromptUpdateRequest(BaseModel):
    clinic_id: str
    prompt: str
    secret_key: str

class HeartbeatRequest(BaseModel):
    clinic_id: str
    session_id: str

class LeadReadRequest(BaseModel):
    read: bool

class LeadNoteRequest(BaseModel):
    note: str

class LeadStatusRequest(BaseModel):
    status: str

class BlockIPRequest(BaseModel):
    ip: str
    secret_key: str

class SessionTagRequest(BaseModel):
    tag: str
    secret_key: str

class TypingRequest(BaseModel):
    clinic_id: str
    session_id: str

class AdminMessageRequest(BaseModel):
    clinic_id: str
    session_id: str
    message: str
    secret_key: str

class BulkDeleteLeadsRequest(BaseModel):
    lead_ids: list[str]
    secret_key: str

class UpdateKeyRequest(BaseModel):
    current_key: str
    new_key: str

class FeedbackRequest(BaseModel):
    clinic_id: str
    type: str # 'up' or 'down'
    message: Optional[str] = None

class MaintenanceRequest(BaseModel):
    clinic_id: str
    enabled: bool
    secret_key: str

class CustomCSSRequest(BaseModel):
    clinic_id: str
    css: str
    secret_key: str

# --- AGENT PERSONAS ---
DEFAULT_AGENTS = {
    "lemon-main": {
        "name": "Lisa",
        "role": "Business Consultant",
        "prompt": "You are Lisa, a senior AI business consultant for Lemon Techno. Your goal is to help business owners understand how AI agents can automate their support, sales, and booking workflows. You are professional, enthusiastic, and knowledgeable about SaaS, automation, and ROI. Keep answers concise.",
        "booking_url": "https://calendly.com/lemon-techno/demo"
    },
    "dental-demo": {
        "name": "Sarah",
        "role": "Dental Receptionist",
        "prompt": "You are Sarah, a warm and professional dental receptionist. You help patients book appointments, answer questions about procedures (whitening, implants, cleaning), and handle emergency triage. If a patient mentions pain, ask about severity.",
        "booking_url": "https://calendly.com/lemon-techno/dental-demo"
    },
    "retail-demo": {
        "name": "Emily",
        "role": "Retail Assistant",
        "prompt": "You are Emily, a helpful retail sales associate. You help customers find products, check order status, and handle returns. You are upbeat, use emojis occasionally, and try to upsell matching items.",
        "booking_url": ""
    },
    "beauty-demo": {
        "name": "Chloe",
        "role": "Aesthetics Concierge",
        "prompt": "You are Chloe, a high-end aesthetics concierge for a plastic surgery clinic. You are elegant, discreet, and knowledgeable about Botox, fillers, and surgical procedures. Your goal is to secure consultation bookings.",
        "booking_url": "https://calendly.com/lemon-techno/beauty-demo"
    },
    "realestate-demo": {
        "name": "Jessica",
        "role": "Leasing Agent",
        "prompt": "You are Jessica, a top real estate leasing agent. Your goal is to qualify leads for property viewings. Ask about budget, move-in date, and credit score before scheduling a tour.",
        "booking_url": "https://calendly.com/lemon-techno/realestate-demo"
    },
    "support-demo": {
        "name": "Anna",
        "role": "Tech Support",
        "prompt": "You are Anna, a technical support specialist. You help users troubleshoot login issues, billing questions, and software bugs. You are patient, clear, and step-by-step in your instructions.",
        "booking_url": ""
    }
}

AGENTS = copy.deepcopy(DEFAULT_AGENTS)

def log_system_event(level: str, message: str):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message
    }
    SYSTEM_LOGS.append(entry)
    if len(SYSTEM_LOGS) > 200:
        SYSTEM_LOGS.pop(0)
    print(f"[{level}] {message}")

@app.get("/")
def root():
    print("Root endpoint hit - DentalBot API")
    return {"status": "ok", "service": "DentalBot API"}

@app.get("/public/clinic/{clinic_id}")
def get_clinic_info(clinic_id: str):
    # Return agent info so the widget can adapt (if not overridden by HTML)
    agent = AGENTS.get(clinic_id, AGENTS.get("lemon-main"))
    is_maintenance = MAINTENANCE_MODE.get(clinic_id, False)
    custom_css = CUSTOM_CSS.get(clinic_id, "")
    return {
        "clinic_name": agent["name"],
        "booking_url": agent["booking_url"],
        "logo_url": "", # Avatar is handled by frontend data attributes
        "maintenance_mode": is_maintenance,
        "custom_css": custom_css
    }

@app.post("/chat")
def chat_endpoint(req: ChatRequest, request: Request):
    # Handle Render/Proxy IP headers
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0]
    else:
        client_ip = request.client.host if request.client else "Unknown"

    if client_ip in BLOCKED_IPS:
        raise HTTPException(status_code=403, detail="Access denied")

    if MAINTENANCE_MODE.get(req.clinic_id, False):
         return {
            "reply": "System is currently under maintenance. Please try again later.",
            "booking_url": ""
        }

    # Ensure we always have a valid agent, defaulting to lemon-main
    agent = AGENTS.get(req.clinic_id, AGENTS.get("lemon-main"))
    if not agent:
        # Fallback if even lemon-main is missing (should not happen)
        agent = {"name": "Assistant", "prompt": "You are a helpful assistant.", "booking_url": ""}
    
    # Log user message
    if req.clinic_id not in CHAT_LOGS:
        CHAT_LOGS[req.clinic_id] = {}
    
    # Also log a heartbeat on any message
    if req.clinic_id not in LIVE_SESSIONS:
        LIVE_SESSIONS[req.clinic_id] = {}
    LIVE_SESSIONS[req.clinic_id][req.session_id] = datetime.now()

    # Store IP for this session
    if req.session_id not in SESSION_METADATA:
        SESSION_METADATA[req.session_id] = {"ip": client_ip}

    if req.session_id not in CHAT_LOGS[req.clinic_id]:
        CHAT_LOGS[req.clinic_id][req.session_id] = []
    
    CHAT_LOGS[req.clinic_id][req.session_id].append({"role": "user", "content": req.message, "timestamp": datetime.now().isoformat()})
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "reply": f"[System]: OpenAI API Key missing. I would be {agent['name']} answering: '{req.message}'",
            "booking_url": agent["booking_url"]
        }

    try:
        client = openai.OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": agent["prompt"]},
                {"role": "user", "content": req.message}
            ],
            temperature=0.7,
            max_tokens=250
        )
        reply = completion.choices[0].message.content
        
        # Log assistant reply
        CHAT_LOGS[req.clinic_id][req.session_id].append({"role": "assistant", "content": reply, "timestamp": datetime.now().isoformat()})
        
        return {
            "reply": reply,
            "booking_url": agent["booking_url"]
        }
    except Exception as e:
        log_system_event("ERROR", f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/prompt/{clinic_id}")
def get_agent_prompt(clinic_id: str, key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    agent = AGENTS.get(clinic_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"prompt": agent["prompt"]}

@app.post("/admin/prompt")
def update_agent_prompt(req: PromptUpdateRequest):
    if req.secret_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if req.clinic_id in AGENTS:
        AGENTS[req.clinic_id]["prompt"] = req.prompt
        return {"status": "updated", "agent": AGENTS[req.clinic_id]["name"]}
    raise HTTPException(status_code=404, detail="Agent not found")

@app.post("/admin/prompt/reset")
def reset_agent_prompt(req: PromptUpdateRequest):
    if req.secret_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if req.clinic_id in DEFAULT_AGENTS:
        AGENTS[req.clinic_id]["prompt"] = DEFAULT_AGENTS[req.clinic_id]["prompt"]
        return {"status": "reset", "prompt": AGENTS[req.clinic_id]["prompt"]}
    raise HTTPException(status_code=404, detail="Agent not found")

@app.post("/admin/settings/key")
def update_admin_key(req: UpdateKeyRequest):
    global ADMIN_KEY
    if req.current_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    ADMIN_KEY = req.new_key
    return {"status": "updated"}

@app.get("/admin/maintenance/{clinic_id}")
def get_maintenance_status(clinic_id: str, key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"enabled": MAINTENANCE_MODE.get(clinic_id, False)}

@app.post("/admin/maintenance")
def update_maintenance_mode(req: MaintenanceRequest):
    if req.secret_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    MAINTENANCE_MODE[req.clinic_id] = req.enabled
    return {"status": "updated", "enabled": req.enabled}

@app.get("/admin/css/{clinic_id}")
def get_custom_css(clinic_id: str, key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"css": CUSTOM_CSS.get(clinic_id, "")}

@app.post("/admin/css")
def update_custom_css(req: CustomCSSRequest):
    if req.secret_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    CUSTOM_CSS[req.clinic_id] = req.css
    return {"status": "updated"}

def analyze_sentiment(messages):
    # Simple keyword-based sentiment analysis
    text = " ".join([m["content"] for m in messages if m["role"] == "user"]).lower()
    pos_words = {"thanks", "thank", "good", "great", "love", "excellent", "amazing", "helpful", "perfect", "appreciate"}
    neg_words = {"bad", "worst", "terrible", "awful", "hate", "useless", "stupid", "broken", "error", "fail", "slow", "wrong"}
    
    score = 0
    for w in text.split():
        if w in pos_words: score += 1
        if w in neg_words: score -= 1
        
    if score > 0: return "Positive"
    if score < 0: return "Negative"
    return "Neutral"

@app.get("/admin/history/{clinic_id}")
def get_chat_history(clinic_id: str, key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    raw_history = CHAT_LOGS.get(clinic_id, {})
    # Transform list of messages into object with metadata
    # Include IP address in the response
    return {
        sid: {
            "messages": msgs, 
            "sentiment": analyze_sentiment(msgs),
            "ip": SESSION_METADATA.get(sid, {}).get("ip", "Unknown"),
            "tags": SESSION_METADATA.get(sid, {}).get("tags", [])
        }
        for sid, msgs in raw_history.items()
    }

@app.post("/admin/history/{clinic_id}/{session_id}/tags")
def add_session_tag(clinic_id: str, session_id: str, req: SessionTagRequest):
    if req.secret_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if session_id not in SESSION_METADATA:
        SESSION_METADATA[session_id] = {}
    
    tags = SESSION_METADATA[session_id].get("tags", [])
    if req.tag not in tags:
        tags.append(req.tag)
        SESSION_METADATA[session_id]["tags"] = tags
        
    return {"status": "added", "tags": tags}

@app.delete("/admin/history/{clinic_id}/{session_id}/tags/{tag}")
def remove_session_tag(clinic_id: str, session_id: str, tag: str, key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    if session_id in SESSION_METADATA:
        tags = SESSION_METADATA[session_id].get("tags", [])
        if tag in tags:
            tags.remove(tag)
            SESSION_METADATA[session_id]["tags"] = tags
            return {"status": "removed", "tags": tags}
            
    return {"status": "not found", "tags": SESSION_METADATA.get(session_id, {}).get("tags", [])}

@app.post("/admin/block_ip")
def block_ip(req: BlockIPRequest):
    if req.secret_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    BLOCKED_IPS.add(req.ip)
    return {"status": "blocked", "ip": req.ip}

@app.post("/typing")
def report_typing(req: TypingRequest):
    if req.clinic_id not in SESSION_TYPING:
        SESSION_TYPING[req.clinic_id] = {}
    SESSION_TYPING[req.clinic_id][req.session_id] = datetime.now()
    return {"status": "ok"}

@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    if req.clinic_id not in FEEDBACK_STATS:
        FEEDBACK_STATS[req.clinic_id] = {"up": 0, "down": 0}
    
    if req.type == "up":
        FEEDBACK_STATS[req.clinic_id]["up"] += 1
    elif req.type == "down":
        FEEDBACK_STATS[req.clinic_id]["down"] += 1
        
    return {"status": "received"}

@app.get("/admin/feedback/{clinic_id}")
def get_feedback_stats(clinic_id: str, key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return FEEDBACK_STATS.get(clinic_id, {"up": 0, "down": 0})

@app.delete("/admin/feedback/{clinic_id}")
def reset_feedback_stats(clinic_id: str, key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if clinic_id in FEEDBACK_STATS:
        FEEDBACK_STATS[clinic_id] = {"up": 0, "down": 0}
    return {"status": "reset"}

@app.get("/admin/typing_status/{clinic_id}")
def get_typing_status(clinic_id: str, key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    now = datetime.now()
    typing_sessions = []
    if clinic_id in SESSION_TYPING:
        for sid, ts in SESSION_TYPING[clinic_id].items():
            # Consider typing if updated in last 3 seconds
            if now - ts < timedelta(seconds=3):
                typing_sessions.append(sid)
    return {"typing_sessions": typing_sessions}

@app.post("/admin/message")
def send_admin_message(req: AdminMessageRequest):
    if req.secret_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Log to history
    if req.clinic_id not in CHAT_LOGS: CHAT_LOGS[req.clinic_id] = {}
    if req.session_id not in CHAT_LOGS[req.clinic_id]: CHAT_LOGS[req.clinic_id][req.session_id] = []
    
    CHAT_LOGS[req.clinic_id][req.session_id].append({
        "role": "assistant", 
        "content": req.message, 
        "timestamp": datetime.now().isoformat()
    })

    # Queue for widget
    if req.clinic_id not in MESSAGE_QUEUE: MESSAGE_QUEUE[req.clinic_id] = {}
    if req.session_id not in MESSAGE_QUEUE[req.clinic_id]: MESSAGE_QUEUE[req.clinic_id][req.session_id] = []
    MESSAGE_QUEUE[req.clinic_id][req.session_id].append(req.message)
    
    return {"status": "sent"}

@app.post("/heartbeat")
def heartbeat(req: HeartbeatRequest):
    if req.clinic_id not in LIVE_SESSIONS:
        LIVE_SESSIONS[req.clinic_id] = {}
    LIVE_SESSIONS[req.clinic_id][req.session_id] = datetime.now()
    
    # Return queued messages
    messages = []
    if req.clinic_id in MESSAGE_QUEUE and req.session_id in MESSAGE_QUEUE[req.clinic_id]:
        messages = MESSAGE_QUEUE[req.clinic_id][req.session_id]
        MESSAGE_QUEUE[req.clinic_id][req.session_id] = [] # Clear queue
        
    return {"status": "ok", "messages": messages}

@app.get("/admin/live_visitors")
def get_live_visitors(key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    now = datetime.now()
    active_count = 0
    # Clean up old sessions while we're at it
    for clinic_id, sessions in list(LIVE_SESSIONS.items()):
        for session_id, last_seen in list(sessions.items()):
            # Consider active if seen in last 2 minutes
            if now - last_seen < timedelta(minutes=2):
                active_count += 1
            else:
                # Clean up inactive session
                del LIVE_SESSIONS[clinic_id][session_id]
        if not LIVE_SESSIONS[clinic_id]:
            del LIVE_SESSIONS[clinic_id]

    return {"live_visitors": active_count}

@app.delete("/admin/history/{clinic_id}/{session_id}")
def delete_chat_session(clinic_id: str, session_id: str, key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if clinic_id in CHAT_LOGS and session_id in CHAT_LOGS[clinic_id]:
        del CHAT_LOGS[clinic_id][session_id]
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/admin/leads/{clinic_id}")
def get_leads(clinic_id: str, key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Return leads sorted by timestamp desc
    leads = LEADS.get(clinic_id, [])
    return sorted(leads, key=lambda x: x.get("timestamp", ""), reverse=True)

@app.delete("/admin/leads/{clinic_id}/{lead_id}")
def delete_lead(clinic_id: str, lead_id: str, key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if clinic_id in LEADS:
        original_len = len(LEADS[clinic_id])
        LEADS[clinic_id] = [l for l in LEADS[clinic_id] if l.get("id") != lead_id]
        if len(LEADS[clinic_id]) < original_len:
            return {"status": "deleted"}
            
    raise HTTPException(status_code=404, detail="Lead not found")

@app.post("/admin/leads/{clinic_id}/bulk_delete")
def bulk_delete_leads(clinic_id: str, req: BulkDeleteLeadsRequest):
    if req.secret_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if clinic_id in LEADS:
        original_len = len(LEADS[clinic_id])
        LEADS[clinic_id] = [l for l in LEADS[clinic_id] if l.get("id") not in req.lead_ids]
        return {"status": "deleted", "count": original_len - len(LEADS[clinic_id])}
            
    raise HTTPException(status_code=404, detail="Clinic not found")

@app.get("/admin/logs")
def get_system_logs(key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return sorted(SYSTEM_LOGS, key=lambda x: x["timestamp"], reverse=True)

@app.delete("/admin/logs")
def clear_system_logs(key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    SYSTEM_LOGS.clear()
    return {"status": "cleared"}

@app.put("/admin/leads/{clinic_id}/{lead_id}/read")
def update_lead_read_status(clinic_id: str, lead_id: str, req: LeadReadRequest, key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if clinic_id in LEADS:
        for lead in LEADS[clinic_id]:
            if lead.get("id") == lead_id:
                lead["read"] = req.read
                return {"status": "updated", "read": req.read}
            
    raise HTTPException(status_code=404, detail="Lead not found")

@app.put("/admin/leads/{clinic_id}/{lead_id}/note")
def update_lead_note(clinic_id: str, lead_id: str, req: LeadNoteRequest, key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if clinic_id in LEADS:
        for lead in LEADS[clinic_id]:
            if lead.get("id") == lead_id:
                lead["note"] = req.note
                return {"status": "updated", "note": req.note}
            
    raise HTTPException(status_code=404, detail="Lead not found")

@app.put("/admin/leads/{clinic_id}/{lead_id}/status")
def update_lead_status(clinic_id: str, lead_id: str, req: LeadStatusRequest, key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if clinic_id in LEADS:
        for lead in LEADS[clinic_id]:
            if lead.get("id") == lead_id:
                lead["status"] = req.status
                return {"status": "updated", "lead_status": req.status}
            
    raise HTTPException(status_code=404, detail="Lead not found")

@app.post("/leads")
def submit_lead(req: LeadRequest, request: Request):
    # Handle Render/Proxy IP headers
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0]
    else:
        client_ip = request.client.host if request.client else "Unknown"

    if req.clinic_id not in LEADS:
        LEADS[req.clinic_id] = []
    lead_data = req.model_dump()
    lead_data["timestamp"] = datetime.now().isoformat()
    lead_data["id"] = str(uuid.uuid4())
    lead_data["read"] = False
    lead_data["status"] = "New"
    lead_data["ip"] = client_ip
    LEADS[req.clinic_id].append(lead_data)
    log_system_event("INFO", f"Lead received [{req.clinic_id}]: {req.email}")
    return {"status": "received"}