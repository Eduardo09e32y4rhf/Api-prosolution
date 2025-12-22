import httpx
from app.config import OPENAI_API_KEY

OPENAI_URL = "https://api.openai.com/v1/chat/completions"

async def generate_with_chatgpt(prompt: str):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(OPENAI_URL, headers=headers, json=payload)

    data = res.json()
    return data["choices"][0]["message"]["content"]