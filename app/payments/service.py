from app.database.session import AsyncSessionLocal
from app.database.models.payment import Payment
from app.config import settings
import uuid


from app.payments.mercadopago_client import MercadoPagoClient

async def create_pix_payment(amount: float, email: str, description: str | None = None):
    """
    Cria um pagamento PIX usando a integração com Mercado Pago
    """
    
    # 1. Criar pagamento no Mercado Pago
    mp_client = MercadoPagoClient()
    
    payload = {
        "transaction_amount": amount,
        "description": description or "Pagamento Prosolution",
        "payment_method_id": "pix",
        "payer": {
            "email": email
        }
    }
    

    mp_response = await mp_client.create_payment(payload)
    
    if mp_response.status_code not in (200, 201):
        # Em caso de erro, podemos levantar exceção ou retornar erro
        return {
            "error": "Erro ao criar pagamento no Mercado Pago",
            "details": mp_response.json()

        }
        
    mp_data = mp_response.json()
    
    # 2. Salvar no Banco de Dados
    async with AsyncSessionLocal() as session:
        payment = Payment(
            email=email,
            amount=amount,
            status=mp_data.get("status", "pending"),
            external_id=str(mp_data.get("id"))
        )

        session.add(payment)
        await session.commit()
        await session.refresh(payment)

        return {
            "payment_id": payment.id,
            "external_id": payment.external_id,
            "status": payment.status,
            "amount": payment.amount,
            "qr_code": mp_data.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code"),
            "qr_code_base64": mp_data.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64"),
            "ticket_url": mp_data.get("point_of_interaction", {}).get("transaction_data", {}).get("ticket_url"),
            "message": "PIX gerado com sucesso",
        }

