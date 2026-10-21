import os
import re
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path

from cryptography.fernet import Fernet

# Configuração de teste antes de importar a aplicação (Settings lê o ambiente no import)
_tmpdir = tempfile.mkdtemp(prefix="prosolution-tests-")
os.environ.update(
    {
        "ENVIRONMENT": "test",
        "SECRET_KEY": "test-secret-key",
        "ENCRYPTION_KEY": Fernet.generate_key().decode(),
        # TEST_DATABASE_URL permite rodar a mesma suíte contra Postgres (como no CI)
        "DATABASE_URL": os.environ.get("TEST_DATABASE_URL") or f"sqlite+aiosqlite:///{Path(_tmpdir) / 'test.db'}",
        "ASAAS_WEBHOOK_TOKEN": "webhook-test-token",
        "ASAAS_API_KEY": "asaas-test-key",
        "APP_BASE_URL": "https://testserver",
    }
)

import httpx  # noqa: E402
import pytest  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.rate_limit import limiter  # noqa: E402
from app.database.models import Base  # noqa: E402
from app.database.session import AsyncSessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

CSRF_RE = re.compile(r'name="csrf_token" value="([^"]+)"')
PASSWORD = "senha-forte-123"


@pytest.fixture(autouse=True)
async def _reset_state() -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    limiter.reset()
    yield


@pytest.fixture
async def db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


class Client(httpx.AsyncClient):
    """Cliente de teste que se comporta como um navegador: guarda cookies e envia o token CSRF."""

    csrf_token: str | None = None

    async def fetch_csrf(self, path: str = "/") -> str:
        resp = await self.get(path)
        match = CSRF_RE.search(resp.text)
        assert match, f"token CSRF não encontrado em {path}"
        self.csrf_token = match.group(1)
        return self.csrf_token

    async def submit(self, url: str, data: dict[str, str] | None = None) -> httpx.Response:
        if self.csrf_token is None:
            await self.fetch_csrf()
        return await self.post(url, data={**(data or {}), "csrf_token": self.csrf_token or ""})

    async def register(self, email: str, password: str = PASSWORD) -> httpx.Response:
        return await self.submit("/auth/register", {"email": email, "password": password})

    async def login(self, email: str, password: str = PASSWORD) -> httpx.Response:
        return await self.submit("/auth/login", {"email": email, "password": password})


def make_client() -> Client:
    # https: o cookie de sessão é Secure e não seria enviado em http
    return Client(transport=httpx.ASGITransport(app=app), base_url="https://testserver")


@pytest.fixture
async def client() -> AsyncIterator[Client]:
    async with make_client() as c:
        yield c


@pytest.fixture
async def other_client() -> AsyncIterator[Client]:
    async with make_client() as c:
        yield c
