from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Routers
from app.auth.routes import router as auth_router
from app.dashboard.routes import router as dashboard_router
from app.payments.webhooks import router as payments_webhook_router

# Database
from app.database.base import init_db
from app.database.session import get_db
from app.database.repositories.user_repo import UserRepository

app = FastAPI(title="Prosolution API")

# === STARTUP ===
@app.on_event("startup")
async def startup():
    await init_db()

# === STATIC / TEMPLATES ===
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# === HOME ===
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# === ROUTERS ===
app.include_router(auth_router, prefix="/auth")
app.include_router(dashboard_router)
app.include_router(payments_webhook_router, prefix="/api")

# === API TEST ===
@app.get("/api")
async def api_root():
    return {"status": "🚀 Prosolution API online"}

# === USERS (TESTE) ===
@app.get("/api/users")
async def list_users(db=Depends(get_db)):
    return await UserRepository(db).list_all()
