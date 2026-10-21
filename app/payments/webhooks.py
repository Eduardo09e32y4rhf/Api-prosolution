import logging
import secrets
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.models.payment import Payment
from app.database.models.user import User
from app.database.session import get_db
from app.payments.subscriptions import confirm_payment, reverse_payment

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Payments"])

CONFIRMED_EVENTS = {"PAYMENT_RECEIVED", "PAYMENT_CONFIRMED"}
REVERSAL_EVENTS = {"PAYMENT_REFUNDED": "REFUNDED", "PAYMENT_DELETED": "DELETED"}


def verify_asaas_token(asaas_access_token: str | None = Header(default=None)) -> None:
    """O Asaas envia no header `asaas-access-token` o token cadastrado no painel do webhook."""
    expected = settings.ASAAS_WEBHOOK_TOKEN
    if not expected:
        # Falha fechada: sem token configurado, nenhum webhook é aceito
        logger.error("ASAAS_WEBHOOK_TOKEN não configurado; webhook rejeitado")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Webhook não configurado")
    if not asaas_access_token or not secrets.compare_digest(asaas_access_token, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token do webhook inválido")


@router.post("/asaas/webhook", dependencies=[Depends(verify_asaas_token)])
async def asaas_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Recebe notificações do Asaas sobre status de pagamentos."""
    payload = await request.json()
    event = payload.get("event")
    payment_data = payload.get("payment") or {}
    payment_id = payment_data.get("id")
    customer_id = payment_data.get("customer")

    if not payment_id or not customer_id:
        return {"status": "ignored", "reason": "Missing data"}

    user = (await db.execute(select(User).where(User.asaas_customer_id == customer_id))).scalar_one_or_none()
    if not user:
        return {"status": "ignored", "reason": "User not found"}

    # Só aceitamos cobranças geradas por nós para este usuário
    payment = (
        await db.execute(select(Payment).where(Payment.external_id == payment_id, Payment.user_id == user.id))
    ).scalar_one_or_none()
    if not payment:
        return {"status": "ignored", "reason": "Payment not found"}

    if event in CONFIRMED_EVENTS:
        extended = confirm_payment(user, payment)
        await db.commit()
        return {"status": "success", "message": "Subscription extended" if extended else "Already processed"}

    if event == "PAYMENT_OVERDUE":
        # A assinatura não é estendida e expira sozinha em current_period_end
        payment.status = "OVERDUE"
        await db.commit()
        return {"status": "success", "message": "Payment overdue"}

    if event in REVERSAL_EVENTS:
        reverse_payment(user, payment, REVERSAL_EVENTS[event])
        await db.commit()
        return {"status": "success", "message": "Subscription revoked"}

    return {"status": "ignored", "reason": "Unhandled event type"}
