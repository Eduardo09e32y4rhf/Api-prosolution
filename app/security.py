import bcrypt
import os
from datetime import datetime, timedelta
from jose import jwt
from fastapi import Request, HTTPException, status
from app.core.config import settings

ALGORITHM = "HS256"

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def hash_password(password: str) -> str:
    return get_password_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')[:72]
    hash_bytes = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False

def create_token(data: dict, expires_delta_hours: float | None = None) -> str:
    to_encode = data.copy()
    if expires_delta_hours is not None:
        expire = datetime.utcnow() + timedelta(hours=expires_delta_hours)
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.TOKEN_EXPIRES_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    return payload

def get_current_user_from_cookie(request: Request):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida ou expirada")
    return payload
