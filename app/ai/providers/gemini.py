import google.generativeai as genai
from app.config import GEMINI_API_KEY
from app.ai.providers.base import AIProvider

genai.configure(api_key=GEMINI_API_KEY)

class GeminiProvider(AIProvider):
    def generate(self, prompt: str) -> str:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text.strip()
