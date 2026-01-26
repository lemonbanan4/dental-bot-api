"""
Clean, minimal FastAPI app that properly uses modular routes.
This replaces the broken main.py with extensive duplication.
"""
import os
import redis.asyncio as redis
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

from app.config import settings
from app.routes import chat, leads, admin, clinics, public

# Initialize FastAPI app
app = FastAPI(
    title="Dental Bot API",
    description="AI-powered dental clinic chat and lead management",
    version="1.0.0",
)

# CORS Configuration: Allow specified origins or all if configured
origins = settings.origins_list()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event: Initialize Redis connection
@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection for rate limiting and caching."""
    redis_url = settings.redis_url
    if redis_url:
        try:
            # Create Redis connection pool
            pool = redis.ConnectionPool.from_url(redis_url, decode_responses=False)
            app.state.redis = redis.Redis(connection_pool=pool)
            # Test connection
            await app.state.redis.ping()
            print("✅ Redis connected successfully")
        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}. Rate limiting will use in-memory fallback.")
            app.state.redis = None
    else:
        print("ℹ️  Redis URL not configured. Rate limiting will use in-memory fallback.")
        app.state.redis = None

# Shutdown event: Close Redis connection
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up Redis connection on shutdown."""
    if hasattr(app.state, "redis") and app.state.redis:
        await app.state.redis.close()

# Register API route modules
app.include_router(chat.router)
app.include_router(leads.router)
app.include_router(leads.router2)
app.include_router(admin.router)
app.include_router(clinics.router)
app.include_router(public.router)

# Mount static files (widget.js, admin.html, etc.)
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint for monitoring."""
    redis_ok = False
    if hasattr(app.state, "redis") and app.state.redis:
        try:
            await app.state.redis.ping()
            redis_ok = True
        except Exception:
            pass
    
    return {
        "status": "ok",
        "env": settings.app_env,
        "redis_connected": redis_ok,
    }

@app.get("/healthz")
async def healthz():
    """Kubernetes liveness probe endpoint."""
    return {"status": "ok"}

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    """Root endpoint."""
    return {
        "service": "Dental Bot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }

# ============================================================================
# BACKWARD COMPATIBILITY ENDPOINTS (for old widget.js versions)
# ============================================================================
# These endpoints support the old widget.js API format
# They're kept for backward compatibility with deployed widgets

# In-memory storage for backward compat endpoints
_OLD_API_CHAT_LOGS: Dict[str, list] = {}
_OLD_API_LIVE_SESSIONS: Dict[str, Dict[str, datetime]] = {}
_OLD_API_MESSAGE_QUEUE: Dict[str, Dict[str, list]] = {}
_OLD_API_FEEDBACK_STATS: Dict[str, Dict[str, int]] = {}

class OldChatRequest(BaseModel):
    """Old widget.js chat request format."""
    clinic_id: str
    message: str
    session_id: str
    metadata: Optional[Dict[str, Any]] = None

class OldHeartbeatRequest(BaseModel):
    """Old widget.js heartbeat request format."""
    clinic_id: str
    session_id: str

class OldFeedbackRequest(BaseModel):
    """Old widget.js feedback request format."""
    clinic_id: str
    type: str  # 'up' or 'down'
    message: Optional[str] = None

class OldTypingRequest(BaseModel):
    """Old widget.js typing indicator format."""
    clinic_id: str
    session_id: str

@app.post("/heartbeat")
async def heartbeat_compat(req: OldHeartbeatRequest):
    """Backward compatibility heartbeat endpoint.
    
    Maintains session alive and returns queued messages.
    Old widget.js expects this endpoint.
    """
    if req.clinic_id not in _OLD_API_LIVE_SESSIONS:
        _OLD_API_LIVE_SESSIONS[req.clinic_id] = {}
    _OLD_API_LIVE_SESSIONS[req.clinic_id][req.session_id] = datetime.now()
    
    # Return queued messages if any
    messages = []
    if req.clinic_id in _OLD_API_MESSAGE_QUEUE and req.session_id in _OLD_API_MESSAGE_QUEUE[req.clinic_id]:
        messages = _OLD_API_MESSAGE_QUEUE[req.clinic_id][req.session_id]
        _OLD_API_MESSAGE_QUEUE[req.clinic_id][req.session_id] = []
        
    return {"status": "ok", "messages": messages}

@app.post("/typing")
async def typing_compat(req: OldTypingRequest):
    """Backward compatibility typing indicator endpoint.
    
    Old widget.js sends typing status here.
    """
    return {"status": "ok"}

@app.post("/feedback")
async def feedback_compat(req: OldFeedbackRequest):
    """Backward compatibility feedback endpoint.
    
    Old widget.js sends feedback here.
    """
    if req.clinic_id not in _OLD_API_FEEDBACK_STATS:
        _OLD_API_FEEDBACK_STATS[req.clinic_id] = {"up": 0, "down": 0}
    
    if req.type == "up":
        _OLD_API_FEEDBACK_STATS[req.clinic_id]["up"] += 1
    elif req.type == "down":
        _OLD_API_FEEDBACK_STATS[req.clinic_id]["down"] += 1
        
    return {"status": "received"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_env == "dev",
    )
