import hashlib
from datetime import timedelta
from typing import Any

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.timeutils import utcnow
from app.database.models.user import User
from app.database.session import get_db

ALGORITHM = "HS256"
SESSION_COOKIE = "token"
MIN_PASSWORD_LENGTH = 8


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    expire = utcnow() + (expires_delta or timedelta(hours=settings.TOKEN_EXPIRES_HOURS))
    return jwt.encode({**data, "exp": expire}, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Levanta `JWTError` se o token for inválido ou estiver expirado."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def create_session_token(user: User) -> str:
    return create_token({"sub": user.email, "type": "session"})


def _password_fingerprint(user: User) -> str:
    # Muda quando a senha muda, invalidando links de redefinição já usados
    return hashlib.sha256(user.password_hash.encode()).hexdigest()[:16]


def create_password_reset_token(user: User) -> str:
    return create_token(
        {"sub": user.email, "type": "password_reset", "pwd": _password_fingerprint(user)},
        expires_delta=timedelta(minutes=settings.PASSWORD_RESET_EXPIRES_MINUTES),
    )


def password_reset_token_matches(payload: dict[str, Any], user: User) -> bool:
    return payload.get("type") == "password_reset" and payload.get("pwd") == _password_fingerprint(user)


def set_session_cookie(response: Any, user: User) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(user),
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.TOKEN_EXPIRES_HOURS * 3600,
    )


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Dependência das rotas autenticadas: devolve o usuário do cookie de sessão ou 401."""
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise unauthorized
    try:
        payload = decode_token(token)
    except JWTError:
        raise unauthorized from None
    if payload.get("type") != "session" or not payload.get("sub"):
        raise unauthorized

    user = (await db.execute(select(User).where(User.email == payload["sub"]))).scalar_one_or_none()
    if user is None or user.is_active is False:
        raise unauthorized
    return user
