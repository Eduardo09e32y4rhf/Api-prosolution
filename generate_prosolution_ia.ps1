Write-Host "🚀 Gerando Prosolution IA..."

$paths = @(
    "app/ai/providers",
    "app/ai/admin"
)

foreach ($path in $paths) {
    New-Item -ItemType Directory -Force -Path $path | Out-Null
}

Set-Content app/ai/providers/base.py @"
class AIProvider:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError
"@

Set-Content app/ai/providers/gemini.py @"
import google.generativeai as genai
from app.config import GEMINI_API_KEY
from app.ai.providers.base import AIProvider

genai.configure(api_key=GEMINI_API_KEY)

class GeminiProvider(AIProvider):
    def generate(self, prompt: str) -> str:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text.strip()
"@

Set-Content app/ai/providers/openai.py @"
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
"@

Set-Content app/ai/admin/policies.py @"
FORBIDDEN_MARKETING_TOPICS = [
    "politica", "religiao", "ideologia", "lgbt",
    "orientacao sexual", "identidade de genero",
    "violencia", "odio", "seguranca publica",
    "armas", "saude sensivel"
]

def is_forbidden_topic(text: str) -> bool:
    text = text.lower()
    return any(topic in text for topic in FORBIDDEN_MARKETING_TOPICS)
"@

Set-Content app/ai/admin/prompts.py @"
SYSTEM_ADMIN_PROMPT = '''
Você é a IA ADMINISTRADORA GERAL (AI GOVERNANCE ADMIN).

Você NÃO executa código.
Você NÃO altera arquivos.
Você NÃO faz deploy.

Seu papel:
- Avaliar segurança
- Avaliar código
- Avaliar LGPD
- Avaliar riscos jurídicos
- Avaliar bugs prováveis
- Avaliar dependências

No final gere UM PROMPT com:
🔴 OBRIGATÓRIO
🟡 NECESSÁRIO
🟢 MELHORIAS OPCIONAIS
'''
"@

Set-Content app/ai/admin/system_admin.py @"
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
"@

Set-Content app/ai/orchestrator.py @"
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.openai import OpenAIProvider

gemini = GeminiProvider()
openai = OpenAIProvider()

def generate_instagram_content(topic: str) -> dict:
    base = gemini.generate(f"Crie legenda criativa sobre: {topic}")
    improved = openai.generate(f"Melhore com CTA:\n{base}")
    return {"caption": improved}
"@

Set-Content app/ai/routes.py @"
from fastapi import APIRouter
from app.ai.orchestrator import generate_instagram_content
from app.ai.admin.system_admin import evaluate_system

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/instagram-content")
def instagram_content(topic: str):
    return generate_instagram_content(topic)

@router.post("/admin-review")
def admin_review(system_snapshot: dict):
    return {"admin_prompt": evaluate_system(system_snapshot)}
"@

Write-Host "✅ Prosolution IA gerada com sucesso."
