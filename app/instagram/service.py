import httpx
from urllib.parse import urlencode
from app.core.config import settings

class InstagramService:
    def __init__(self):
        self.app_id = settings.INSTAGRAM_APP_ID
        self.app_secret = settings.INSTAGRAM_APP_SECRET
        self.redirect_uri = settings.INSTAGRAM_REDIRECT_URI
        self.base_url = "https://graph.facebook.com/v18.0" # Graph API para contas business vinculadas a pages
        
    def get_authorization_url(self) -> str:
        """Retorna a URL de login do Facebook/Meta com os escopos necessários."""
        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "scope": "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement",
            "response_type": "code"
        }
        return f"https://www.facebook.com/v18.0/dialog/oauth?{urlencode(params)}"
        
    async def exchange_code_for_token(self, code: str) -> str:
        """Troca o código de autorização por um Access Token de curta duração e logo troca por longa duração."""
        # 1. Trocar code por short-lived token
        token_url = f"{self.base_url}/oauth/access_token"
        params = {
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "redirect_uri": self.redirect_uri,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(token_url, params=params)
            data = response.json()
            
            if "error" in data:
                raise Exception(f"Erro ao obter token: {data['error'].get('message')}")
                
            short_lived_token = data.get("access_token")
            
            # 2. Trocar short-lived por long-lived token
            long_params = {
                "grant_type": "fb_exchange_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "fb_exchange_token": short_lived_token
            }
            
            long_res = await client.get(token_url, params=long_params)
            long_data = long_res.json()
            
            if "error" in long_data:
                raise Exception(f"Erro ao gerar token de longa duração: {long_data['error'].get('message')}")
                
            return long_data.get("access_token")

    async def get_instagram_business_account_id(self, access_token: str) -> str:
        """Busca o ID da conta Instagram associada à página do Facebook do usuário."""
        async with httpx.AsyncClient() as client:
            # Pegar as páginas que o usuário gerencia
            pages_url = f"{self.base_url}/me/accounts"
            pages_res = await client.get(pages_url, params={"access_token": access_token})
            pages_data = pages_res.json()
            
            if not pages_data.get("data"):
                raise Exception("Nenhuma página do Facebook encontrada para este usuário.")
                
            # Procura uma página que tenha instagram_business_account
            for page in pages_data["data"]:
                page_id = page["id"]
                ig_url = f"{self.base_url}/{page_id}?fields=instagram_business_account"
                ig_res = await client.get(ig_url, params={"access_token": access_token})
                ig_data = ig_res.json()
                
                if "instagram_business_account" in ig_data:
                    return ig_data["instagram_business_account"]["id"]
                    
            raise Exception("Nenhuma conta comercial do Instagram vinculada à(s) sua(s) página(s) do Facebook.")

    async def publish_post(self, ig_account_id: str, access_token: str, image_url: str, caption: str) -> str:
        """Faz o upload da mídia e publica no Instagram."""
        async with httpx.AsyncClient() as client:
            # 1. Criar container de mídia
            media_url = f"{self.base_url}/{ig_account_id}/media"
            media_params = {
                "image_url": image_url,
                "caption": caption,
                "access_token": access_token
            }
            media_res = await client.post(media_url, params=media_params)
            media_data = media_res.json()
            
            if "error" in media_data:
                raise Exception(f"Erro ao enviar mídia: {media_data['error'].get('message')}")
                
            creation_id = media_data.get("id")
            
            # 2. Publicar container
            publish_url = f"{self.base_url}/{ig_account_id}/media_publish"
            publish_params = {
                "creation_id": creation_id,
                "access_token": access_token
            }
            publish_res = await client.post(publish_url, params=publish_params)
            publish_data = publish_res.json()
            
            if "error" in publish_data:
                raise Exception(f"Erro ao publicar mídia: {publish_data['error'].get('message')}")
                
            return publish_data.get("id")
