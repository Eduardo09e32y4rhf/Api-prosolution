import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from app.core.config import settings

class AIEngine:
    def __init__(self):
        # Usamos o modelo gpt-4o-mini por padrão para textos curtos e rápidos
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            # Em modo de desenvolvimento sem chave, podemos simular
            self.llm = None
        else:
            self.llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o-mini", openai_api_key=api_key)
            
    def _build_system_prompt(self, business, brand, topic: str) -> str:
        """Constrói o prompt unindo todo o contexto da empresa"""
        
        prompt_template = """
Você é um Social Media expert e um Copywriter profissional de alta conversão.
Sua missão é escrever um post para o Instagram baseado no perfil exato do seu cliente.

=== PERFIL DA EMPRESA ===
Segmento: {segment}
Público-alvo: {audience}
Objetivo da empresa: {objective}
Principais produtos: {products}
Principais serviços: {services}

=== IDENTIDADE DA MARCA ===
Tom de voz obrigatório: {tone}
Estilo visual/palavras-chave: {style}
Usar Emojis: {emojis}

=== REGRAS RESTRITAS ===
- NUNCA use as seguintes palavras proibidas: {forbidden_words}
- O post deve ter uma formatação limpa, com parágrafos curtos.
- O post deve terminar obrigatoriamente com esta chamada para ação (CTA): "{cta}"

=== TEMA DO POST ===
Escreva uma legenda atraente e persuasiva sobre: {topic}

Apenas retorne o texto da legenda, sem aspas e sem explicações extras.
"""
        return PromptTemplate(
            template=prompt_template,
            input_variables=[
                "segment", "audience", "objective", "products", "services", 
                "tone", "style", "emojis", "forbidden_words", "cta", "topic"
            ]
        ).format(
            segment=business.segment if business and business.segment else "Não informado",
            audience=business.audience if business and business.audience else "Público geral",
            objective=business.objective if business and business.objective else "Engajamento",
            products=business.products if business and business.products else "Não informado",
            services=business.services if business and business.services else "Não informado",
            tone=brand.tone if brand and brand.tone else "Profissional",
            style=brand.style if brand and brand.style else "Padrão",
            emojis="SIM, seja generoso nos emojis" if (brand and brand.emojis) else "NÃO, é expressamente proibido usar emojis.",
            forbidden_words=brand.forbidden_words if brand and brand.forbidden_words else "Nenhuma restrição",
            cta=brand.cta if brand and brand.cta else "Comente abaixo o que achou!",
            topic=topic
        )

    async def generate_post(self, business, brand, topic: str) -> str:
        prompt_text = self._build_system_prompt(business, brand, topic)
        
        if not self.llm:
            return f"[MODO SIMULADO - Sem OPENAI_API_KEY]\n\nOlha que post incrível sobre '{topic}' para a empresa de '{business.segment if business else 'Teste'}'!\n\n(Coloque sua chave no .env para gerar conteúdo real.)"
            
        try:
            response = await self.llm.ainvoke(prompt_text)
            return response.content
        except Exception as e:
            return f"Erro ao gerar post: {str(e)}"
