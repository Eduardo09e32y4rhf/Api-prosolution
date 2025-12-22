FORBIDDEN_MARKETING_TOPICS = [
    "politica", "religiao", "ideologia", "lgbt",
    "orientacao sexual", "identidade de genero",
    "violencia", "odio", "seguranca publica",
    "armas", "saude sensivel"
]

def is_forbidden_topic(text: str) -> bool:
    text = text.lower()
    return any(topic in text for topic in FORBIDDEN_MARKETING_TOPICS)
