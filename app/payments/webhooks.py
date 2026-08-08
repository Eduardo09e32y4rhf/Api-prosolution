from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.session import get_db
from app.database.models.user import User
from app.database.models.payment import Payment

router = APIRouter()

@router.post("/asaas/webhook")
async def asaas_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Recebe notificações do Asaas sobre status de pagamentos"""
    payload = await request.json()
    
    event = payload.get("event")
    payment_data = payload.get("payment", {})
    
    payment_id = payment_data.get("id")
    customer_id = payment_data.get("customer")
    
    if not payment_id or not customer_id:
        return {"status": "ignored", "reason": "Missing data"}

    # Busca o usuário pelo customer_id do asaas
    user = (await db.execute(select(User).where(User.asaas_customer_id == customer_id))).scalar_one_or_none()
    
    if not user:
        return {"status": "ignored", "reason": "User not found"}

    # Se o pagamento foi recebido ou confirmado
    if event in ["PAYMENT_RECEIVED", "PAYMENT_CONFIRMED"]:
        user.is_vip = True
        
        # Busca se já tem o payment registrado para atualizar o status
        payment = (await db.execute(select(Payment).where(Payment.external_id == payment_id))).scalar_one_or_none()
        if payment:
            payment.status = "PAID"
            
        await db.commit()
        return {"status": "success", "message": "User upgraded to VIP"}

    # Se o pagamento atrasou ou falhou
    elif event in ["PAYMENT_OVERDUE", "PAYMENT_DELETED", "PAYMENT_REFUNDED"]:
        user.is_vip = False
        payment = (await db.execute(select(Payment).where(Payment.external_id == payment_id))).scalar_one_or_none()
        if payment:
            payment.status = "FAILED"
            
        await db.commit()
        return {"status": "success", "message": "User VIP revoked"}

    return {"status": "ignored", "reason": "Unhandled event type"}
