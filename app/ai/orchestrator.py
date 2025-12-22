
from app.ai.providers.gemini import GeminiProvider

def generate_instagram_content(prompt: str) -> str:
    provider = GeminiProvider()
    return provider.generate(prompt)
