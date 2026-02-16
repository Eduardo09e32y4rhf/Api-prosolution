from sqlalchemy.ext.asyncio import AsyncSession

from payments.mercadopago_client import MercadoPagoClient
from payments.models import Payment


def _extract_pix_data(mp_json: dict) -> dict:
    poi = mp_json.get("point_of_interaction") or {}
    tx = poi.get("transaction_data") or {}

    return {
        "mp_payment_id": str(mp_json.get("id")) if mp_json.get("id") is not None else None,
        "status": mp_json.get("status") or "pending",
        "qr_code": tx.get("qr_code"),
        "qr_code_base64": tx.get("qr_code_base64"),
        "ticket_url": tx.get("ticket_url"),
    }


async def create_pix_payment(
    db: AsyncSession,
    *,
    amount: float,
    description: str,
    email: str,
) -> dict:
    mp = MercadoPagoClient()

    payload = {
        "transaction_amount": float(amount),
        "description": description,
        "payment_method_id": "pix",
        "payer": {"email": email},
    }

    mp_json = await mp.create_payment(payload)
    pix = _extract_pix_data(mp_json)

    payment = Payment(
        email=email,
        amount=amount,
        description=description,
        status=pix["status"] or "pending",
        mp_payment_id=pix["mp_payment_id"],
        qr_code=pix["qr_code"],
        qr_code_base64=pix["qr_code_base64"],
        ticket_url=pix["ticket_url"],
    )

    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return {
        "payment_id": payment.id,
        "mp_payment_id": payment.mp_payment_id,
        "status": payment.status,
        "amount": float(payment.amount),
        "description": payment.description,
        "qr_code": payment.qr_code,
        "qr_code_base64": payment.qr_code_base64,
        "ticket_url": payment.ticket_url,
    }
