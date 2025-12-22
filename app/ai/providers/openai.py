from openai import OpenAI
from app.config import OPENAI_API_KEY
from app.ai.providers.base import AIProvider

client = OpenAI(api_key=OPENAI_API_KEY)

class OpenAIProvider(AIProvider):
    def generate(self, prompt: str) -> str:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
