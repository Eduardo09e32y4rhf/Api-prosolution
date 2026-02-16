from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from config import settings

ALGORITHM = "HS256"
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd.verify(password, hashed)


def create_token(data: dict) -> str:
    payload = dict(data)
    payload["exp"] = datetime.utcnow() + timedelta(hours=settings.TOKEN_EXPIRES_HOURS)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
