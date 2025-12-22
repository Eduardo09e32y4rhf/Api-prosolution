
import google.generativeai as genai
from app.config import settings
from app.ai.providers.base import AIProvider

genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiProvider(AIProvider):
    def generate(self, prompt: str) -> str:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text
