"""Proteção CSRF no padrão "double submit cookie".

O middleware garante que todo navegador tenha um cookie `csrf_token`; os templates
renderizam o mesmo valor num campo oculto e `verify_csrf` exige que os dois batam
em toda requisição que altera estado.
"""

import secrets

from fastapi import HTTPException, Request, status
from markupsafe import Markup, escape
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import settings

CSRF_COOKIE = "csrf_token"
CSRF_FIELD = "csrf_token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        token = request.cookies.get(CSRF_COOKIE) or ""
        is_new = not token
        if is_new:
            token = secrets.token_urlsafe(32)
        request.state.csrf_token = token

        response = await call_next(request)
        if is_new:
            response.set_cookie(CSRF_COOKIE, token, httponly=True, secure=settings.COOKIE_SECURE, samesite="lax")
        return response


async def verify_csrf(request: Request) -> None:
    if request.method in SAFE_METHODS:
        return
    cookie_token = request.cookies.get(CSRF_COOKIE)
    form_token = (await request.form()).get(CSRF_FIELD)
    if not cookie_token or not isinstance(form_token, str) or not secrets.compare_digest(cookie_token, form_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token CSRF inválido")


def csrf_input(request: Request) -> Markup:
    token = getattr(request.state, "csrf_token", "")
    # O token é escapado antes de entrar no Markup
    return Markup(f'<input type="hidden" name="{CSRF_FIELD}" value="{escape(token)}">')  # noqa: S704
