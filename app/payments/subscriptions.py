from datetime import timedelta

from app.core.config import settings
from app.core.timeutils import utcnow
from app.database.models.payment import Payment
from app.database.models.subscription import Subscription
from app.database.models.user import User


def confirm_payment(user: User, payment: Payment) -> bool:
    """Marca o pagamento como pago e estende a assinatura por PRO_PLAN_DAYS.

    Idempotente: o Asaas reenvia eventos e manda RECEIVED depois de CONFIRMED para o
    mesmo pagamento, então um pagamento já pago não estende o período de novo.
    """
    if payment.status == "PAID":
        return False
    payment.status = "PAID"

    now = utcnow()
    subscription = user.subscription
    if subscription is None:
        subscription = Subscription(user_id=user.id)
        user.subscription = subscription

    # Renovação antecipada soma ao período que ainda resta
    start = subscription.current_period_end if subscription.is_active and subscription.current_period_end else now
    subscription.current_period_end = start + timedelta(days=settings.PRO_PLAN_DAYS)
    subscription.status = "active"
    return True


def reverse_payment(user: User, payment: Payment, new_status: str) -> None:
    """Estorno/exclusão de um pagamento já pago encerra a assinatura imediatamente."""
    was_paid = payment.status == "PAID"
    payment.status = new_status
    if was_paid and user.subscription is not None:
        user.subscription.status = "canceled"
        user.subscription.current_period_end = utcnow()
