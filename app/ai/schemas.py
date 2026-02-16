from pydantic import BaseModel

class GeminiInstagramSchema(BaseModel):
    niche: str
    objective: str
    language: str = "pt-BR"