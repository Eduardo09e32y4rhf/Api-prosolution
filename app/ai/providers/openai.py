
from openai import OpenAI
from app.config import settings
from app.ai.providers.base import AIProvider

class OpenAIProvider(AIProvider):
    def generate(self, prompt: str) -> str:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content
