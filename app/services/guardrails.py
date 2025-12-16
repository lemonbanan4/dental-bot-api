import re

EMERGENCY_PATTERNS = [
    r"can't breathe", r"trouble breathing", r"swelling.*throat",
    r"uncontrolled bleeding", r"severe bleeding",
    r"fainting", r"passed out", 
]
SYMPTOM_PATTERNS = [
    r"toothache", r"pain", r"swelling", r"fever", r"infection",
    r"pus", r"bleeding gums", r"broken tooth", r"abscess",
]

def is_emergency(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in EMERGENCY_PATTERNS)

def is_symptom_or_diagnosis_request(text: str) -> bool:
    t = text.lower()
    # crude but effective for MVP
    if "should i" in t or "what should" in t or "do i need" in t:
        return True
    return any(re.search(p, t) for p in SYMPTOM_PATTERNS)
