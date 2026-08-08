import httpx
import os
from typing import Optional, Dict, Any

class AsaasService:
    def __init__(self):
        # Em produção, essas variáveis devem vir do .env
        self.api_key = os.getenv("ASAAS_API_KEY", "$aact_YTU5YTE0M2M2N2I4MTliNDgwYjZiMTg5NzMwYTEwZDQ6OjAwMDAwMDAwMDAwMDAwMDAwMDA6OiRhYWNoXzM0NTY3ODkw")
        # Por padrão usa sandbox
        self.base_url = os.getenv("ASAAS_BASE_URL", "https://sandbox.asaas.com/api/v3")
        self.headers = {
            "access_token": self.api_key,
            "Content-Type": "application/json"
        }

    async def create_customer(self, name: str, email: str, cpf_cnpj: str = None) -> Optional[str]:
        """Cria um cliente no Asaas e retorna o asaas_customer_id"""
        payload = {
            "name": name,
            "email": email
        }
        if cpf_cnpj:
            payload["cpfCnpj"] = cpf_cnpj
            
        async with httpx.AsyncClient() as client:
            res = await client.post(f"{self.base_url}/customers", json=payload, headers=self.headers)
            if res.status_code in [200, 201]:
                return res.json().get("id")
            print(f"[Asaas Error] create_customer: {res.text}")
            return None

    async def create_payment_link(self, customer_id: str, value: float, description: str) -> Optional[Dict[str, Any]]:
        """Gera uma cobrança via PIX e retorna o payload com o QRCode/Link"""
        payload = {
            "customer": customer_id,
            "billingType": "PIX",
            "value": value,
            "dueDate": "2030-12-31", # Vencimento longo para assinatura padrão
            "description": description
        }
        
        async with httpx.AsyncClient() as client:
            res = await client.post(f"{self.base_url}/payments", json=payload, headers=self.headers)
            if res.status_code in [200, 201]:
                data = res.json()
                return {
                    "payment_id": data.get("id"),
                    "invoice_url": data.get("invoiceUrl"),
                    "status": data.get("status")
                }
            print(f"[Asaas Error] create_payment_link: {res.text}")
            return None
            
    async def get_pix_qrcode(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Pega o QR Code PIX de um pagamento gerado"""
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{self.base_url}/payments/{payment_id}/pixQrCode", headers=self.headers)
            if res.status_code == 200:
                return res.json()
            return None
