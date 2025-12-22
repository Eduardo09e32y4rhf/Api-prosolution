from fastapi import HTTPException
from app.payments.mercadopago_client import MercadoPagoClient

client = MercadoPagoClient()


async def create_pix_payment(amount: float, description: str, email: str):
    payload = {
        "transaction_amount": amount,
        "description": description,
        "payment_method_id": "pix",
        "payer": {
            "email": email
        }
    }

    response = await client.create_payment(payload)
    data = response.json()

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=400,
            detail={
                "stage": "mercado_pago_payment",
                "error": data
            }
        )

    transaction_data = data.get("point_of_interaction", {}).get("transaction_data", {})

    return {
        "payment_id": data.get("id"),
        "status": data.get("status"),
        "qr_code": transaction_data.get("qr_code"),
        "qr_code_base64": transaction_data.get("qr_code_base64"),
    }