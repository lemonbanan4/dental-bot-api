from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routes import chat, clinics, leads

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

# Serve static assets (e.g., widget.js)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
def health():
    return {"ok": True, "env": settings.app_env}


