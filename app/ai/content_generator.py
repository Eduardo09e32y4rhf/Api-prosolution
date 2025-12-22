from app.ai.gemini_service import generate_with_gemini
from app.ai.chatgpt_service import generate_with_chatgpt

async def generate_content(niche: str, objective: str):
    prompt = f"""
Crie uma legenda para Instagram.
Nicho: {niche}
Objetivo: {objective}
Inclua hashtags.
"""

    try:
        return await generate_with_gemini(prompt)
    except:
        return await generate_with_chatgpt(prompt)