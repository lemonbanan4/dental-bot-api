import httpx
from app.config import settings
import json

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


async def chat_completion_stream(system: str, messages: list[dict]):
    """Stream tokens from the OpenAI chat completions API.

    Yields text chunks (strings) as they arrive from the provider.
    """
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
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", OPENAI_URL, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                raw = line.strip()
                if raw.startswith("data:"):
                    raw = raw[len("data:"):].strip()
                if raw == "[DONE]":
                    break
                try:
                    obj = json.loads(raw)
                except Exception:
                    continue
                try:
                    delta = obj.get("choices", [])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content
                except Exception:
                    continue