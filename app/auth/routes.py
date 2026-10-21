import logging
from urllib.parse import urlencode

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.csrf import verify_csrf
from app.core.email import send_email
from app.core.rate_limit import limiter
from app.core.templates import templates
from app.database.repositories.user_repo import UserRepository
from app.database.session import get_db
from app.security import (
    MIN_PASSWORD_LENGTH,
    SESSION_COOKIE,
    create_password_reset_token,
    decode_token,
    hash_password,
    password_reset_token_matches,
    set_session_cookie,
    verify_password,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Auth"], dependencies=[Depends(verify_csrf)])

RECOVER_MESSAGE = "Se o e-mail existir, um link de recuperação foi enviado."


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _redirect_home(**params: str) -> RedirectResponse:
    return RedirectResponse(f"/?{urlencode(params)}", status_code=302)


@router.post("/register")
@limiter.limit(settings.REGISTER_RATE_LIMIT)
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    email = _normalize_email(email)
    if len(password) < MIN_PASSWORD_LENGTH:
        return _redirect_home(error="weak_password")

    repo = UserRepository(db)
    if await repo.get_by_email(email):
        return _redirect_home(error="email_taken")

    user = await repo.create_user(email=email, password_hash=hash_password(password))
    resp = RedirectResponse("/dashboard", status_code=302)
    set_session_cookie(resp, user)
    return resp


@router.post("/login")
@limiter.limit(settings.LOGIN_RATE_LIMIT)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    user = await UserRepository(db).get_by_email(_normalize_email(email))
    if not user or not verify_password(password, user.password_hash) or user.is_active is False:
        return _redirect_home(error="invalid_credentials")

    resp = RedirectResponse("/dashboard", status_code=302)
    set_session_cookie(resp, user)
    return resp


@router.post("/logout")
async def logout() -> RedirectResponse:
    resp = RedirectResponse("/", status_code=302)
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@router.get("/recover-password", response_class=HTMLResponse)
async def recover_password_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "forgot_password.html", {})


@router.post("/recover-password", response_class=HTMLResponse)
@limiter.limit(settings.RECOVER_PASSWORD_RATE_LIMIT)
async def recover_password(
    request: Request,
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    user = await UserRepository(db).get_by_email(_normalize_email(email))
    if user:
        token = create_password_reset_token(user)
        link = f"{settings.APP_BASE_URL.rstrip('/')}/auth/reset-password?token={token}"
        body = (
            "Olá!\n\n"
            "Recebemos um pedido para redefinir a senha da sua conta Prosolution.\n"
            f"Use o link abaixo em até {settings.PASSWORD_RESET_EXPIRES_MINUTES} minutos:\n\n{link}\n\n"
            "Se não foi você, ignore este e-mail."
        )
        # Envio em segundo plano: a resposta tem o mesmo tempo e conteúdo exista ou não o e-mail
        background_tasks.add_task(send_email, user.email, "Redefinição de senha - Prosolution", body)

    return templates.TemplateResponse(request, "forgot_password.html", {"message": RECOVER_MESSAGE})


@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str = "") -> HTMLResponse:
    return templates.TemplateResponse(request, "reset_password.html", {"token": token})


@router.post("/reset-password", response_class=HTMLResponse, response_model=None)
async def reset_password(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse | RedirectResponse:
    def error(message: str) -> HTMLResponse:
        return templates.TemplateResponse(
            request, "reset_password.html", {"token": token, "error": message}, status_code=400
        )

    if len(new_password) < MIN_PASSWORD_LENGTH:
        return error(f"A senha precisa ter pelo menos {MIN_PASSWORD_LENGTH} caracteres")

    invalid = "Link inválido ou expirado. Solicite uma nova recuperação de senha."
    try:
        payload = decode_token(token)
    except JWTError:
        return error(invalid)

    user = await UserRepository(db).get_by_email(payload.get("sub") or "")
    if not user or not password_reset_token_matches(payload, user):
        return error(invalid)

    user.password_hash = hash_password(new_password)
    await db.commit()
    return _redirect_home(msg="password_reset")
