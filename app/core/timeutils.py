"""Datas são gravadas no banco como UTC "naive"; a conversão para o fuso do usuário
acontece só na entrada (formulários) e na saída (templates)."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.core.config import settings


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def local_tz() -> ZoneInfo:
    return ZoneInfo(settings.APP_TIMEZONE)


def local_to_utc(value: datetime) -> datetime:
    """Converte um datetime "naive" no fuso da aplicação para UTC "naive"."""
    return value.replace(tzinfo=local_tz()).astimezone(UTC).replace(tzinfo=None)


def utc_to_local(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC).astimezone(local_tz())


def format_local(value: datetime | None, fmt: str = "%d/%m/%Y %H:%M") -> str:
    if value is None:
        return ""
    return utc_to_local(value).strftime(fmt)
