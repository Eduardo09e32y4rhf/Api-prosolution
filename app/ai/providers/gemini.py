from google import genai
from app.config import settings
from app.ai.providers.base import AIProvider

class GeminiProvider(AIProvider):
    def __init__(self):
        # Usando a nova biblioteca google-genai
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        # Sugestão: gemini-1.5-flash é mais rápido e barato que o pro
        self.model_id = "gemini-1.5-flash" 

    def generate(self, prompt: str) -> str:
        try:
            # Nova sintaxe de geração
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            return response.text
        except Exception as e:
            # Caso a API falhe, retorna o erro amigável em vez de travar o servidor
            return f"Erro na Prosolution IA: Não foi possível gerar conteúdo agora. (Detalhe: {str(e)})"