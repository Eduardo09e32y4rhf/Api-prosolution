from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import settings

SCOPES = "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement"


class InstagramError(Exception):
    """Erro vindo da Graph API da Meta. A mensagem é técnica: logue, não mostre ao usuário."""


def _raise_on_error(data: dict[str, Any], context: str) -> None:
    if "error" in data:
        raise InstagramError(f"{context}: {data['error'].get('message')}")


class InstagramService:
    def __init__(self) -> None:
        self.app_id = settings.INSTAGRAM_APP_ID
        self.app_secret = settings.INSTAGRAM_APP_SECRET
        self.redirect_uri = settings.INSTAGRAM_REDIRECT_URI
        # Graph API do Facebook: contas Instagram Business são vinculadas a Páginas
        self.base_url = f"{settings.INSTAGRAM_GRAPH_URL.rstrip('/')}/{settings.INSTAGRAM_API_VERSION}"

    def get_authorization_url(self, state: str) -> str:
        """URL de login da Meta. `state` protege o callback contra CSRF."""
        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "scope": SCOPES,
            "response_type": "code",
            "state": state,
        }
        return f"https://www.facebook.com/{settings.INSTAGRAM_API_VERSION}/dialog/oauth?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> str:
        """Troca o código por um token de curta duração e depois por um de longa duração."""
        token_url = f"{self.base_url}/oauth/access_token"
        async with httpx.AsyncClient(timeout=15) as client:
            data = (
                await client.get(
                    token_url,
                    params={
                        "client_id": self.app_id,
                        "client_secret": self.app_secret,
                        "redirect_uri": self.redirect_uri,
                        "code": code,
                    },
                )
            ).json()
            _raise_on_error(data, "Erro ao obter token")

            long_data = (
                await client.get(
                    token_url,
                    params={
                        "grant_type": "fb_exchange_token",
                        "client_id": self.app_id,
                        "client_secret": self.app_secret,
                        "fb_exchange_token": data.get("access_token"),
                    },
                )
            ).json()
            _raise_on_error(long_data, "Erro ao gerar token de longa duração")
            token: str = long_data["access_token"]
            return token

    async def get_instagram_business_account_id(self, access_token: str) -> str:
        """Busca o ID da conta Instagram associada a uma página do Facebook do usuário."""
        async with httpx.AsyncClient(timeout=15) as client:
            pages_data = (
                await client.get(f"{self.base_url}/me/accounts", params={"access_token": access_token})
            ).json()
            if not pages_data.get("data"):
                raise InstagramError("Nenhuma página do Facebook encontrada para este usuário.")

            for page in pages_data["data"]:
                ig_data = (
                    await client.get(
                        f"{self.base_url}/{page['id']}",
                        params={"fields": "instagram_business_account", "access_token": access_token},
                    )
                ).json()
                if "instagram_business_account" in ig_data:
                    account_id: str = ig_data["instagram_business_account"]["id"]
                    return account_id

        raise InstagramError("Nenhuma conta comercial do Instagram vinculada às páginas do Facebook.")

    async def publish_post(self, ig_account_id: str, access_token: str, image_url: str, caption: str) -> str:
        """Cria o container de mídia e o publica no Instagram."""
        async with httpx.AsyncClient(timeout=30) as client:
            media_data = (
                await client.post(
                    f"{self.base_url}/{ig_account_id}/media",
                    params={"image_url": image_url, "caption": caption, "access_token": access_token},
                )
            ).json()
            _raise_on_error(media_data, "Erro ao enviar mídia")

            publish_data = (
                await client.post(
                    f"{self.base_url}/{ig_account_id}/media_publish",
                    params={"creation_id": media_data.get("id"), "access_token": access_token},
                )
            ).json()
            _raise_on_error(publish_data, "Erro ao publicar mídia")
            media_id: str = publish_data["id"]
            return media_id
