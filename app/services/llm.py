import httpx
from app.config import settings

OPENAI_URL = "https://api.openai.com/v1/chat/completions"

async def chat_completion(system: str, messages: list[dict]) -> str:
    if settings.llm_provider.lower() != "openai":
        raise RuntimeError("Only openai provider is implemented in this MVP")
    
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.openai_model,
        "temperature": 0.2,
        "messages": [{"role": "system", "content": system}] + messages,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(OPENAI_URL, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    return data["choices"][0]["message"]["content"]