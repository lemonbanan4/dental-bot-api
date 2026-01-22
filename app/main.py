"""
Clean, minimal FastAPI app that properly uses modular routes.
This replaces the broken main.py with extensive duplication.
"""
import os
import redis.asyncio as redis
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

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Dental Bot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_env == "dev",
    )
