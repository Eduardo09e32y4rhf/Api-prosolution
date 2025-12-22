import httpx
from fastapi import HTTPException
from app.config import GEMINI_API_KEY

GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"

async def generate_with_gemini(prompt: str):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload
        )

    data = res.json()

    if res.status_code != 200:
        raise HTTPException(400, data)

    return data["candidates"][0]["content"]["parts"][0]["text"]