import time
import requests
from app.instagram.client import create_media, publish_media
from app.config import (
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_BASE_URL,
    INSTAGRAM_API_VERSION,
)

BASE_URL = f"{INSTAGRAM_BASE_URL}/{INSTAGRAM_API_VERSION}"


def publish_image(image_url: str, caption: str) -> dict:
    creation_id = create_media(image_url, caption)

    status_url = f"{BASE_URL}/{creation_id}"

    for _ in range(10):
        response = requests.get(
            status_url,
            params={
                "fields": "status_code",
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=10,
        )
        response.raise_for_status()

        status = response.json().get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError("Instagram retornou ERROR ao processar a mídia")

        time.sleep(1)
    else:
        raise TimeoutError("Timeout aguardando processamento da mídia")

    return publish_media(creation_id)