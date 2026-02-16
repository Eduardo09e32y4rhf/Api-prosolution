import httpx

from config import settings


class MercadoPagoClient:
    def __init__(self):
        if not settings.MERCADO_PAGO_ACCESS_TOKEN:
            raise RuntimeError("MERCADO_PAGO_ACCESS_TOKEN não configurado no .env")

        self.base_url = "https://api.mercadopago.com"
        self.headers = {
            "Authorization": f"Bearer {settings.MERCADO_PAGO_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

    async def create_payment(self, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{self.base_url}/v1/payments",
                headers=self.headers,
                json=payload,
            )

        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = {"raw": resp.text}
            raise RuntimeError({"status_code": resp.status_code, "error": detail})

        return resp.json()
