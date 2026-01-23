from openai import AsyncOpenAI
from app.config import settings

# Initialize client with API key from settings
aclient = AsyncOpenAI(api_key=settings.openai_api_key)

async def chat_completion(system: str, messages: list) -> str:
    """
    Generate a chat completion using OpenAI.
    """
    try:
        response = await aclient.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "system", "content": system}] + messages,
            temperature=0.7,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"LLM Error: {e}")
        return "I apologize, but I am having trouble processing your request right now."

async def chat_completion_stream(system: str, messages: list):
    """
    Stream a chat completion using OpenAI.
    """
    try:
        stream = await aclient.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "system", "content": system}] + messages,
            temperature=0.7,
            stream=True,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    except Exception as e:
        print(f"LLM Stream Error: {e}")
        yield "I apologize, but I am having trouble processing your request right now."