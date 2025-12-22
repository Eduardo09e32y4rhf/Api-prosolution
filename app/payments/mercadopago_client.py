import httpx
from app.config import settings


class MercadoPagoClient:
    def __init__(self):
        self.base_url = "https://api.mercadopago.com"
        self.headers = {
            "Authorization": f"Bearer {settings.MERCADO_PAGO_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

    async def create_payment(self, payload: dict):
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}/v1/payments",
                headers=self.headers,
                json=payload,
            )

        return response