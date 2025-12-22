from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.openai import OpenAIProvider

gemini = GeminiProvider()
openai = OpenAIProvider()

def generate_instagram_content(topic: str) -> dict:
    base = gemini.generate(f"Crie legenda criativa sobre: {topic}")
    improved = openai.generate(f"Melhore com CTA:\n{base}")
    return {"caption": improved}
