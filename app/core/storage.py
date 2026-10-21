"""Armazenamento de imagens dos posts: disco local ou S3 compatível (Cloudflare R2, AWS S3...).

O Instagram baixa a imagem pela URL pública na hora de publicar, então o arquivo precisa estar
acessível pela internet. O banco guarda só a *chave* (`posts/<user>/<uuid>.jpg`); a URL é montada
na hora, assim trocar de domínio ou de bucket não quebra os posts já criados.
"""

import asyncio
import logging
import re
import uuid
from pathlib import Path
from typing import Any, Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)

KEY_RE = re.compile(r"^posts/\d+/[0-9a-f]{32}\.jpg$")


def new_image_key(user_id: int) -> str:
    # uuid4 não é adivinhável: a imagem é pública, mas só quem tem a URL a encontra
    return f"posts/{user_id}/{uuid.uuid4().hex}.jpg"


class Storage(Protocol):
    async def save(self, key: str, data: bytes) -> None: ...

    async def delete(self, key: str) -> None: ...

    def public_url(self, key: str) -> str: ...


class LocalStorage:
    def __init__(self, root: str, base_url: str):
        self.root = Path(root).resolve()
        self.base_url = base_url.rstrip("/")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if not KEY_RE.match(key):
            raise ValueError(f"chave de imagem inválida: {key!r}")
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError(f"chave fora do diretório de mídia: {key!r}")
        return path

    async def save(self, key: str, data: bytes) -> None:
        def write() -> None:
            path = self._path(key)
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_bytes(data)
            tmp.replace(path)  # troca atômica: nunca serve um arquivo pela metade

        await asyncio.to_thread(write)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._path(key).unlink, True)

    def public_url(self, key: str) -> str:
        return f"{self.base_url}/media/{key}"


class S3Storage:
    def __init__(self, bucket: str, public_base_url: str, client: Any = None):
        self.bucket = bucket
        self.public_base_url = public_base_url.rstrip("/")
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            import boto3

            self._client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL or None,  # "" (variável vazia no .env) = endpoint padrão da AWS
                region_name=settings.S3_REGION,
                aws_access_key_id=settings.S3_ACCESS_KEY_ID,
                aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            )
        return self._client

    async def save(self, key: str, data: bytes) -> None:
        if not KEY_RE.match(key):
            raise ValueError(f"chave de imagem inválida: {key!r}")
        await asyncio.to_thread(
            self.client.put_object,
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType="image/jpeg",
            CacheControl="public, max-age=31536000, immutable",  # a chave nunca é reaproveitada
        )

    async def delete(self, key: str) -> None:
        if not KEY_RE.match(key):
            raise ValueError(f"chave de imagem inválida: {key!r}")
        await asyncio.to_thread(self.client.delete_object, Bucket=self.bucket, Key=key)

    def public_url(self, key: str) -> str:
        return f"{self.public_base_url}/{key}"


def build_storage() -> Storage:
    if settings.STORAGE_BACKEND == "s3":
        missing = [
            name
            for name in ("S3_BUCKET", "S3_PUBLIC_BASE_URL", "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY")
            if not getattr(settings, name)
        ]
        if missing:
            raise RuntimeError(f"STORAGE_BACKEND=s3 exige: {', '.join(missing)}")
        assert settings.S3_BUCKET and settings.S3_PUBLIC_BASE_URL  # noqa: S101 (já validado acima, para o mypy)
        return S3Storage(settings.S3_BUCKET, settings.S3_PUBLIC_BASE_URL)
    if settings.STORAGE_BACKEND != "local":
        raise RuntimeError(f"STORAGE_BACKEND inválido: {settings.STORAGE_BACKEND!r} (use 'local' ou 's3')")
    if settings.ENVIRONMENT == "production":
        logger.warning("STORAGE_BACKEND=local em produção: as imagens ficam só neste servidor. Prefira s3.")
    return LocalStorage(settings.MEDIA_ROOT, settings.APP_BASE_URL)


storage: Storage = build_storage()
