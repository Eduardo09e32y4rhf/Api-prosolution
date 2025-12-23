import requests
from app.config import settings

BASE_URL = f"{settings.INSTAGRAM_BASE_URL}/{settings.INSTAGRAM_API_VERSION}"

def create_media(image_url: str, caption: str) -> str:
    url = f"{BASE_URL}/{settings.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"

    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
    }

    r = requests.post(url, data=payload, timeout=30)

    if r.status_code != 200:
        raise RuntimeError(r.text)

    return r.json()["id"]

def publish_media(creation_id: str):
    url = f"{BASE_URL}/{settings.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish"

    payload = {
        "creation_id": creation_id,
        "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
    }

    r = requests.post(url, data=payload, timeout=30)

    if r.status_code != 200:
        raise RuntimeError(r.text)

    return r.json()
