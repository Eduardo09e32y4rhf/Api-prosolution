import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.auth.routes import router as auth_router
from app.core.config import settings
from app.core.csrf import CSRFMiddleware
from app.core.limits import MaxBodySizeMiddleware
from app.core.observability import init_sentry
from app.core.rate_limit import limiter
from app.core.storage import LocalStorage, storage
from app.core.templates import templates
from app.dashboard.posts import router as posts_router
from app.dashboard.routes import router as dashboard_router
from app.database.session import AsyncSessionLocal
from app.legal.routes import router as legal_router
from app.payments.webhooks import router as payments_webhook_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)
init_sentry("web")

app = FastAPI(title="Prosolution API", docs_url=None if settings.ENVIRONMENT == "production" else "/docs")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(CSRFMiddleware)
# Adicionado por último = mais externo: recusa uploads gigantes antes de qualquer parsing
app.add_middleware(MaxBodySizeMiddleware, max_bytes=(settings.MAX_UPLOAD_MB + 2) * 1024 * 1024)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> Response:
    if exc.status_code == 401 and request.url.path.startswith("/dashboard"):
        return RedirectResponse(url="/", status_code=302)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)


app.mount("/static", StaticFiles(directory="static"), name="static")
if isinstance(storage, LocalStorage):
    # Com armazenamento local o próprio app serve as imagens (o Instagram as baixa daqui)
    app.mount("/media", StaticFiles(directory=storage.root), name="media")


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "login.html", {})


@app.api_route("/health", methods=["GET", "HEAD"], response_model=None)
async def health() -> dict[str, str] | JSONResponse:
    """Usado pelo healthcheck do Docker e por monitores externos: também confere o banco."""
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check: banco de dados indisponível")
        return JSONResponse(status_code=503, content={"status": "error", "database": "unavailable"})
    return {"status": "ok", "database": "ok"}


app.include_router(auth_router, prefix="/auth")
app.include_router(dashboard_router)
app.include_router(posts_router)
app.include_router(legal_router)
app.include_router(payments_webhook_router, prefix="/api")
