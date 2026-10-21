import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class AsaasNotConfiguredError(RuntimeError):
    pass


class AsaasService:
    def __init__(self) -> None:
        if not settings.ASAAS_API_KEY:
            raise AsaasNotConfiguredError("ASAAS_API_KEY não configurada")
        self.base_url = settings.ASAAS_BASE_URL.rstrip("/")
        self.headers = {"access_token": settings.ASAAS_API_KEY, "Content-Type": "application/json"}

    async def create_customer(self, name: str, email: str, cpf_cnpj: str | None = None) -> str | None:
        """Cria um cliente no Asaas e retorna o asaas_customer_id."""
        payload = {"name": name, "email": email}
        if cpf_cnpj:
            payload["cpfCnpj"] = cpf_cnpj

        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(f"{self.base_url}/customers", json=payload, headers=self.headers)
        if res.status_code in (200, 201):
            customer_id: str | None = res.json().get("id")
            return customer_id
        logger.error("[Asaas] create_customer falhou (%s): %s", res.status_code, res.text)
        return None

    async def create_payment_link(self, customer_id: str, value: Decimal, description: str) -> dict[str, Any] | None:
        """Gera uma cobrança PIX e retorna id, link da fatura e status."""
        payload = {
            "customer": customer_id,
            "billingType": "PIX",
            "value": float(value),
            "dueDate": (date.today() + timedelta(days=settings.ASAAS_DUE_DAYS)).isoformat(),
            "description": description,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(f"{self.base_url}/payments", json=payload, headers=self.headers)
        if res.status_code in (200, 201):
            data = res.json()
            return {"payment_id": data.get("id"), "invoice_url": data.get("invoiceUrl"), "status": data.get("status")}
        logger.error("[Asaas] create_payment_link falhou (%s): %s", res.status_code, res.text)
        return None
