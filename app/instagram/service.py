from app.instagram.client import create_media, publish_media
from app.config import settings

def publish_image(image_url: str, caption: str):
    if not settings.INSTAGRAM_ACCESS_TOKEN:
        raise RuntimeError("Instagram não configurado")

    creation_id = create_media(image_url, caption)
    return publish_media(creation_id)
