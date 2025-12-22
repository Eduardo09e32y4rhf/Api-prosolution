from app.ai.content_generator import generate_post
from app.database.post_repository import save_post


def run_post(client_id=None, manual=False):
    content = generate_post()
    source = "fallback" if "fallback" in content.lower() else "openai"
    mode = "manual" if manual else "automatic"

    if client_id:
        save_post(client_id, content, source, mode)

    print("[POST]", content)
