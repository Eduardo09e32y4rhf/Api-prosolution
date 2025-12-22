
from app.ai.orchestrator import generate_instagram_content

def run():
    content = generate_instagram_content("Post institucional")
    print(content)
