from app.ai.providers.gemini import GeminiProvider

def generate_instagram_content(topic: str) -> dict:
    provider = GeminiProvider()
    
    # Criamos um "Super Prompt" que dá inteligência à IA
    super_prompt = f"""
    Você é o especialista em marketing da Prosolution IA. 
    Crie um post de alta conversão para o Instagram sobre o tema: {topic}.
    
    Responda no seguinte formato:
    1. LEGENDA: (Com emojis e gatilhos mentais)
    2. IDEIA DE IMAGEM/REEL: (O que deve aparecer visualmente)
    3. HASHTAGS: (As 5 melhores para este nicho)
    4. CTA: (Uma chamada para ação irresistível)
    """
    
    result = provider.generate(super_prompt)
    return {"topic": topic, "content": result}