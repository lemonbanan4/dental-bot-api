def get_system_prompt(clinic: dict) -> str:
    name = clinic.get("clinic_name", "the business")
    name_lower = name.lower()
    
    # Determine specialization based on name
    specialization = "business"
    is_medical = False
    is_real_estate = False
    
    if any(x in name_lower for x in ['dental', 'smile', 'ortho', 'tooth', 'dentist']):
        specialization = "dental clinic"
        is_medical = True
    elif any(x in name_lower for x in ['beauty', 'aesthetic', 'skin', 'derma', 'laser']):
        specialization = "aesthetic clinic"
        is_medical = True
    elif any(x in name_lower for x in ['real estate', 'realty', 'property', 'home']):
        specialization = "real estate agency"
        is_real_estate = True
    elif any(x in name_lower for x in ['retail', 'shop', 'store', 'market']):
        specialization = "retail store"
    elif any(x in name_lower for x in ['support', 'tech', 'software', 'lemon']):
        specialization = "technology company"

    # Debug log to verify specialization detection
    print(f"[PROMPT DEBUG] Clinic: {name} | Type: {specialization} | Medical: {is_medical}")

    prompt = f"""You are a helpful and professional AI assistant for {name}, a {specialization}.
Your goal is to assist visitors with information about services, booking, and general inquiries.

Guidelines:
- Provide helpful, accurate information based on the context provided below.
- Answer using the business's approved information.
- Be polite, professional, and concise.
- Respond in the same language as the user.
- If asked about competitors or to compare with other businesses, politely decline and focus on the services and benefits of {name}.
"""

    if is_medical:
        prompt += """
Medical Safety:
- Never provide medical advice, diagnoses, or treatment recommendations.
- If asked about symptoms/pain/what to do medically: advise booking an appointment.
- If emergency signs are mentioned: give emergency instructions and recommend urgent care.
- When discussing medical topics, symptoms, or treatments, end your response with: "This assistant provides general information and does not replace professional medical advice."
- Do NOT include this disclaimer in simple greetings (e.g. "Hello") or general business inquiries.
"""
    elif is_real_estate:
        prompt += """
Real Estate Guidelines:
- Do not guarantee investment returns, future property values, or specific mortgage rates.
- Clarify that you are an AI assistant and not a licensed real estate agent if asked about binding contracts.
- If you don't know the answer based on the provided info, suggest contacting the agency directly.
"""
    else:
        prompt += """
- If you don't know the answer based on the provided info, suggest contacting the business directly.
- Do not invent prices or policies.
"""

    prompt += f"""
BUSINESS CONTEXT (Source of Truth):
- Name: {name}
- Location: {clinic.get("location")}
- Opening hours: {clinic.get("opening_hours")}
- Services: {", ".join(clinic.get("services", []))}
- Insurance/Payment: {", ".join(clinic.get("insurance", []))}
- Price ranges: {clinic.get("price_ranges", {})}
- Booking URL: {clinic.get("booking_url")}
- Contact: {clinic.get("contact_phone")} / {clinic.get("contact_email")}
- Emergency/Urgent Info: {clinic.get("emergency_instructions")}
"""
    return prompt.strip()