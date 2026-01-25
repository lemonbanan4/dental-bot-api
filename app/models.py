from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ChatMessage(BaseModel):
    role: str # "User" | "assistant"
    content: str

class ChatRequest(BaseModel):
    clinic_id: str = Field(..., min_length=3)
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(default=None, max_length=128)
    locale_hint: Optional[str] = Field(default=None, max_length=32)
    metadata: Optional[Dict[str, Any]] = None # e.g. page_url

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    handoff: bool = False
    handoff_reason: Optional[str] = None

class ClinicProfile(BaseModel):
    clinic_id: str
    clinic_name: str
    location: str
    opening_hours: str
    services: List[str]
    insurance: List[str]
    price_ranges: Dict[str, str] # e.g. {"consultation": "500-900 SEK"}
    languages: List[str] # ["sv", "en"]
    booking_url: str
    emergency_instructions: str
    contact_phone: str
    contact_email: str

class ClinicUpsertRequest(ClinicProfile):
    pass

class LeadRequest(BaseModel):
    clinic_id: str
    session_id: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    message: Optional[str] = None

class LeadResponse(BaseModel):
    ok: bool = True

class FeedbackRequest(BaseModel):
    clinic_id: str
    session_id: str
    rating: str  # "up" or "down"
    comment: Optional[str] = None
