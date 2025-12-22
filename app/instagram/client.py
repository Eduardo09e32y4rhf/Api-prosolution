import requests
from app.config import settings

# 🔹 Usa o objeto settings para acessar as variáveis do .env
BASE_URL = f"{settings.INSTAGRAM_BASE_URL}/{settings.INSTAGRAM_API_VERSION}"


def create_media(image_url: str, caption: str) -> str:
    """
    Cria um media object (imagem + legenda) no Instagram Graph API.
    Retorna o ID de criação (creation_id) para ser publicado depois.
    """
    url = f"{BASE_URL}/{settings.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"

    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
    }

    response = requests.post(
        url,
        data=payload,  # application/x-www-form-urlencoded
        timeout=30,
    )

    # ⚠️ Trata erro explícito da Graph API
    if response.status_code != 200:
        try:
            error_info = response.json().get("error", {})
            raise RuntimeError(
                f"Instagram error {error_info.get('code')}: {error_info.get('message')}"
            )
        except ValueError:
            raise RuntimeError(
                f"Instagram error {response.status_code}: {response.text}"
            )

    data = response.json()
    creation_id = data.get("id")

    if not creation_id:
        raise RuntimeError(f"Instagram response sem id: {data}")

    return creation_id


def publish_media(creation_id: str) -> dict:
    """
    Publica o media object criado anteriormente.
    """
    url = f"{BASE_URL}/{settings.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish"

    response = requests.post(
        url,
        data={
            "creation_id": creation_id,
            "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json()