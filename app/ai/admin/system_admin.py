from app.ai.providers.openai import OpenAIProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.admin.prompts import SYSTEM_ADMIN_PROMPT

openai = OpenAIProvider()
gemini = GeminiProvider()

def evaluate_system(system_snapshot: dict) -> str:
    tech = openai.generate(f"Analise tecnicamente:\n{system_snapshot}")
    product = gemini.generate(f"Avalie produto e UX:\n{system_snapshot}")

    final = openai.generate(
        SYSTEM_ADMIN_PROMPT +
        "\nANÁLISE TÉCNICA:\n" + tech +
        "\nANÁLISE PRODUTO:\n" + product
    )
    return final
