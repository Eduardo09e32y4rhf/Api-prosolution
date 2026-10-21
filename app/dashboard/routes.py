import logging
import secrets
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.engine import AIEngine, AIGenerationError
from app.core.config import settings
from app.core.csrf import verify_csrf
from app.core.templates import templates
from app.core.timeutils import format_local, local_to_utc, utc_to_local
from app.database.models.ai_log import AILog
from app.database.models.brand_profile import BrandProfile
from app.database.models.business import Business
from app.database.models.payment import Payment
from app.database.models.post import Post
from app.database.models.user import User
from app.database.session import get_db
from app.instagram.service import InstagramService
from app.payments.asaas import AsaasNotConfiguredError, AsaasService
from app.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(verify_csrf)])

IG_STATE_COOKIE = "ig_oauth_state"


def _user_context(user: User) -> dict[str, Any]:
    return {"email": user.email, "name": user.display_name}


async def _get_business(db: AsyncSession, user: User) -> Business | None:
    return (await db.execute(select(Business).where(Business.user_id == user.id))).scalar_one_or_none()


async def _get_brand(db: AsyncSession, user: User) -> BrandProfile | None:
    return (await db.execute(select(BrandProfile).where(BrandProfile.user_id == user.id))).scalar_one_or_none()


async def _get_own_post(db: AsyncSession, user: User, post_id: int) -> Post:
    post = (await db.execute(select(Post).where(Post.id == post_id, Post.user_id == user.id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    return post


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> HTMLResponse:
    business = await _get_business(db, user)
    brand = await _get_brand(db, user)

    posts_count = (await db.execute(select(func.count(Post.id)).where(Post.user_id == user.id))).scalar() or 0
    ai_logs_count = (await db.execute(select(func.count(AILog.id)).where(AILog.user_id == user.id))).scalar() or 0
    recent_posts = (
        (await db.execute(select(Post).where(Post.user_id == user.id).order_by(desc(Post.created_at)).limit(5)))
        .scalars()
        .all()
    )

    activities = [
        {
            "title": f"Post Gerado: {p.title}",
            "status": "Concluído",
            "status_color": "#10b981",
            "date": format_local(p.created_at),
        }
        for p in recent_posts
    ]
    metrics = {
        "instagram_status": "Conectado" if brand and brand.ig_account_id else "Não Conectado",
        "posts_this_month": posts_count,
        "ai_actions": ai_logs_count,
    }
    user_data = {
        **_user_context(user),
        "business_name": business.segment if business and business.segment else "Configurar Empresa",
        "plan": "PRO" if user.is_vip else "Free",
    }
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"user": user_data, "metrics": metrics, "activities": activities, "active_menu": "home"},
    )


# --- CONTEÚDO ---


@router.get("/create", response_class=HTMLResponse)
async def create_content(
    request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> HTMLResponse:
    business = await _get_business(db, user)
    posts = (
        (await db.execute(select(Post).where(Post.user_id == user.id).order_by(desc(Post.created_at)))).scalars().all()
    )
    return templates.TemplateResponse(
        request,
        "create.html",
        {
            "user": _user_context(user),
            "has_setup": bool(business and business.segment),
            "posts": posts,
            "active_menu": "create",
        },
    )


@router.post("/create/generate")
async def generate_content(
    topic: str = Form(..., min_length=1, max_length=500),
    details: str = Form("", max_length=2000),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    business = await _get_business(db, user)
    brand = await _get_brand(db, user)
    full_topic = f"{topic}. Detalhes adicionais: {details}" if details else topic

    try:
        generated_content = await AIEngine().generate_post(business, brand, full_topic)
    except AIGenerationError:
        return RedirectResponse("/dashboard/create?error=ai_fail", status_code=302)

    db.add(AILog(user_id=user.id, provider="openai", prompt=full_topic, response=generated_content))
    db.add(
        Post(
            user_id=user.id,
            title=topic[:50] + "..." if len(topic) > 50 else topic,
            content=generated_content,
            platform="instagram",
        )
    )
    await db.commit()
    return RedirectResponse("/dashboard/create", status_code=302)


@router.get("/calendar", response_class=HTMLResponse)
async def calendar(
    request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> HTMLResponse:
    posts = (await db.execute(select(Post).where(Post.user_id == user.id, Post.status == "scheduled"))).scalars().all()
    # Serializado com |tojson no template: conteúdo gerado pela IA nunca vira JS/HTML executável
    events = [
        {
            "id": str(p.id),
            "title": p.title,
            "start": utc_to_local(p.scheduled_for).replace(tzinfo=None).isoformat() if p.scheduled_for else "",
            "extendedProps": {"content": p.content},
        }
        for p in posts
    ]
    return templates.TemplateResponse(
        request, "calendar.html", {"user": _user_context(user), "events": events, "active_menu": "calendar"}
    )


@router.post("/posts/{post_id}/schedule")
async def schedule_post(
    post_id: int,
    scheduled_for: str = Form(...),
    image_url: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    post = await _get_own_post(db, user, post_id)

    try:
        # O navegador envia "YYYY-MM-DDTHH:MM" no horário local do usuário
        local_dt = datetime.strptime(scheduled_for, "%Y-%m-%dT%H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida") from None

    image_url = image_url.strip()
    if image_url and not image_url.startswith("https://"):
        raise HTTPException(status_code=400, detail="A URL da imagem precisa começar com https://")

    post.scheduled_for = local_to_utc(local_dt)
    post.status = "scheduled"
    if image_url:
        post.image_url = image_url
    await db.commit()
    return RedirectResponse("/dashboard/calendar", status_code=302)


@router.post("/posts/{post_id}/delete")
async def delete_post(
    post_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    post = await _get_own_post(db, user, post_id)
    await db.delete(post)
    await db.commit()
    return RedirectResponse("/dashboard/create", status_code=302)


# --- INSTAGRAM ---

IG_ERRORS = {
    "state": "Sessão de conexão expirada ou inválida. Tente conectar novamente.",
    "denied": "A conexão com o Instagram foi cancelada.",
    "connect_fail": "Não foi possível conectar sua conta do Instagram. Verifique se ela é Business e está "
    "vinculada a uma Página do Facebook.",
}


@router.get("/instagram", response_class=HTMLResponse)
async def instagram_view(
    request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> HTMLResponse:
    brand = await _get_brand(db, user)
    return templates.TemplateResponse(
        request,
        "instagram.html",
        {
            "user": _user_context(user),
            "is_connected": bool(brand and brand.ig_access_token and brand.ig_account_id),
            "error_message": IG_ERRORS.get(request.query_params.get("error", "")),
            "active_menu": "instagram",
        },
    )


@router.get("/instagram/connect")
async def instagram_connect(user: User = Depends(get_current_user)) -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    resp = RedirectResponse(InstagramService().get_authorization_url(state))
    resp.set_cookie(IG_STATE_COOKIE, state, max_age=600, httponly=True, secure=settings.COOKIE_SECURE, samesite="lax")
    return resp


@router.get("/instagram/callback")
async def instagram_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    def finish(url: str) -> RedirectResponse:
        resp = RedirectResponse(url, status_code=302)
        resp.delete_cookie(IG_STATE_COOKIE)
        return resp

    expected_state = request.cookies.get(IG_STATE_COOKIE)
    if not state or not expected_state or not secrets.compare_digest(state, expected_state):
        return finish("/dashboard/instagram?error=state")
    if not code:
        return finish("/dashboard/instagram?error=denied")

    try:
        ig_service = InstagramService()
        access_token = await ig_service.exchange_code_for_token(code)
        account_id = await ig_service.get_instagram_business_account_id(access_token)
    except Exception:
        logger.exception("Falha no callback OAuth do Instagram (user_id=%s)", user.id)
        return finish("/dashboard/instagram?error=connect_fail")

    brand = await _get_brand(db, user)
    if not brand:
        brand = BrandProfile(user_id=user.id)
        db.add(brand)
    brand.ig_access_token = access_token
    brand.ig_account_id = account_id
    await db.commit()
    return finish("/dashboard/instagram")


@router.post("/instagram/disconnect")
async def instagram_disconnect(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    brand = await _get_brand(db, user)
    if brand:
        brand.ig_access_token = None
        brand.ig_account_id = None
        await db.commit()
    return RedirectResponse("/dashboard/instagram", status_code=302)


# --- ASSINATURA ---


@router.get("/subscription", response_class=HTMLResponse)
async def subscription_view(request: Request, user: User = Depends(get_current_user)) -> HTMLResponse:
    subscription = user.subscription
    return templates.TemplateResponse(
        request,
        "subscription.html",
        {
            "user": _user_context(user),
            "is_vip": user.is_vip,
            "expires_at": format_local(subscription.current_period_end, "%d/%m/%Y")
            if subscription and user.is_vip
            else None,
            "plan_price": settings.PRO_PLAN_PRICE,
            "plan_days": settings.PRO_PLAN_DAYS,
            "active_menu": "subscription",
        },
    )


@router.post("/subscription/upgrade")
async def subscription_upgrade(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    """Gera uma cobrança PIX de PRO_PLAN_DAYS dias. Assinante ativo pode renovar antecipadamente."""
    try:
        asaas = AsaasService()
    except AsaasNotConfiguredError:
        logger.error("Upgrade solicitado mas ASAAS_API_KEY não está configurada")
        return RedirectResponse("/dashboard/subscription?error=asaas_fail", status_code=302)

    if not user.asaas_customer_id:
        user.asaas_customer_id = await asaas.create_customer(name=user.email, email=user.email)
        if not user.asaas_customer_id:
            return RedirectResponse("/dashboard/subscription?error=asaas_fail", status_code=302)
        await db.commit()

    payment_data = await asaas.create_payment_link(
        user.asaas_customer_id, settings.PRO_PLAN_PRICE, f"Prosolution PRO - {settings.PRO_PLAN_DAYS} dias"
    )
    if not payment_data:
        return RedirectResponse("/dashboard/subscription?error=payment_creation_fail", status_code=302)

    db.add(
        Payment(
            user_id=user.id,
            email=user.email,
            amount=settings.PRO_PLAN_PRICE,
            status=payment_data["status"],
            external_id=payment_data["payment_id"],
        )
    )
    await db.commit()
    return RedirectResponse(payment_data["invoice_url"], status_code=302)


# --- CONFIGURAÇÕES ---


@router.get("/settings", response_class=HTMLResponse)
async def settings_view(
    request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "user": _user_context(user),
            "business": await _get_business(db, user),
            "brand": await _get_brand(db, user),
            "active_menu": "settings",
        },
    )


@router.post("/settings/business")
async def update_business(
    request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    form = await request.form()
    business = await _get_business(db, user)
    if not business:
        business = Business(user_id=user.id)
        db.add(business)

    for field in ("segment", "products", "services", "audience", "city", "whatsapp", "objective"):
        value = form.get(field)
        setattr(business, field, value if isinstance(value, str) else None)

    await db.commit()
    return RedirectResponse("/dashboard/settings?msg=empresa_salva", status_code=302)


@router.post("/settings/brand")
async def update_brand(
    request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    form = await request.form()
    brand = await _get_brand(db, user)
    if not brand:
        brand = BrandProfile(user_id=user.id)
        db.add(brand)

    for field in ("tone", "style", "forbidden_words", "cta"):
        value = form.get(field)
        setattr(brand, field, value if isinstance(value, str) else None)
    brand.emojis = form.get("emojis") == "on"

    await db.commit()
    return RedirectResponse("/dashboard/settings?msg=marca_salva", status_code=302)
