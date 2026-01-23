EMERGENCY_KEYWORDS = [
    "bleeding", "choking", "unconscious", "heart attack", "stroke", 
    "breathing", "ambulance", "911", "emergency", "severe pain", "trauma"
]

MEDICAL_KEYWORDS = [
    "diagnose", "symptom", "treatment", "medicine", "prescription", 
    "infection", "swelling", "pain", "hurt", "ache", "disease"
]

def is_emergency(text: str) -> bool:
    """Check if the text contains emergency keywords."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in EMERGENCY_KEYWORDS)

def is_symptom_or_diagnosis_request(text: str) -> bool:
    """Check if the text is asking for medical advice/diagnosis."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in MEDICAL_KEYWORDS)