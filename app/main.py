from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routes import chat, clinics, leads, public, admin
from app.supabase_db import get_supabase_client
from app.config import settings

import asyncio

_redis = None



app = FastAPI(title="Dental Bot API", version="0.1.0")

origins = settings.origins_list()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(clinics.router)
app.include_router(leads.router)
app.include_router(leads.router2)
app.include_router(admin.router)
app.include_router(public.router)


# Serve static assets (e.g., widget.js)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
def health():
    return {"ok": True, "env": settings.app_env}


@app.get("/debug/clinics")
def debug_clinics():
    sb = get_supabase_client()
    res = sb.table("clinics").select("clinic_id,clinic_name").limit(50).execute()
    return {"clinics": res.data}


@app.get("/")
def root():
    return {
        "service": "Dental Bot API",
        "status": "running",
        "health": "/health"
    }


@app.on_event("startup")
async def _connect_redis():
    # Connect to Redis if REDIS_URL provided
    if settings.redis_url:
        try:
            import redis.asyncio as aioredis
            app.state.redis = aioredis.from_url(settings.redis_url)
            # quick ping to validate connection
            await app.state.redis.ping()
            print("Connected to Redis")
        except Exception as e:
            print("Warning: could not connect to Redis:", e)


@app.on_event("shutdown")
async def _close_redis():
    r = getattr(app.state, 'redis', None)
    if r is not None:
        try:
            await r.close()
        except Exception:
            pass

