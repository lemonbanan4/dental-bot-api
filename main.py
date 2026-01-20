import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import copy
from fastapi import FastAPI, HTTPException
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

@app.get("/")
def root():
    return {"status": "ok", "service": "DentalBot API"}

@app.get("/public/clinic/{clinic_id}")
def get_clinic_info(clinic_id: str):
    # Return agent info so the widget can adapt (if not overridden by HTML)
    agent = AGENTS.get(clinic_id, AGENTS.get("lemon-main"))
    return {
        "clinic_name": agent["name"],
        "booking_url": agent["booking_url"],
        "logo_url": "" # Avatar is handled by frontend data attributes
    }

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    agent = AGENTS.get(req.clinic_id, AGENTS.get("lemon-main"))
    
    # Log user message
    if req.clinic_id not in CHAT_LOGS:
        CHAT_LOGS[req.clinic_id] = {}
    
    # Also log a heartbeat on any message
    if req.clinic_id not in LIVE_SESSIONS:
        LIVE_SESSIONS[req.clinic_id] = {}
    LIVE_SESSIONS[req.clinic_id][req.session_id] = datetime.now()

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
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/prompt/{clinic_id}")
def get_agent_prompt(clinic_id: str, key: str):
    if key != "lemon-secret":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    agent = AGENTS.get(clinic_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"prompt": agent["prompt"]}

@app.post("/admin/prompt")
def update_agent_prompt(req: PromptUpdateRequest):
    if req.secret_key != "lemon-secret":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if req.clinic_id in AGENTS:
        AGENTS[req.clinic_id]["prompt"] = req.prompt
        return {"status": "updated", "agent": AGENTS[req.clinic_id]["name"]}
    raise HTTPException(status_code=404, detail="Agent not found")

@app.post("/admin/prompt/reset")
def reset_agent_prompt(req: PromptUpdateRequest):
    if req.secret_key != "lemon-secret":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if req.clinic_id in DEFAULT_AGENTS:
        AGENTS[req.clinic_id]["prompt"] = DEFAULT_AGENTS[req.clinic_id]["prompt"]
        return {"status": "reset", "prompt": AGENTS[req.clinic_id]["prompt"]}
    raise HTTPException(status_code=404, detail="Agent not found")

@app.get("/admin/history/{clinic_id}")
def get_chat_history(clinic_id: str, key: str):
    if key != "lemon-secret":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return CHAT_LOGS.get(clinic_id, {})

@app.post("/heartbeat")
def heartbeat(req: HeartbeatRequest):
    if req.clinic_id not in LIVE_SESSIONS:
        LIVE_SESSIONS[req.clinic_id] = {}
    LIVE_SESSIONS[req.clinic_id][req.session_id] = datetime.now()
    return {"status": "ok"}

@app.get("/admin/live_visitors")
def get_live_visitors(key: str):
    if key != "lemon-secret":
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
    if key != "lemon-secret":
        raise HTTPException(status_code=401, detail="Unauthorized")
    if clinic_id in CHAT_LOGS and session_id in CHAT_LOGS[clinic_id]:
        del CHAT_LOGS[clinic_id][session_id]
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Session not found")

@app.post("/leads")
def submit_lead(req: LeadRequest):
    # Here you would save to a database or send an email
    print(f"LEAD RECEIVED [{req.clinic_id}]: {req.name} - {req.email}")
    return {"status": "received"}