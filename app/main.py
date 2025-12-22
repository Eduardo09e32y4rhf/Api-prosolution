from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# === IMPORTS DOS MÓDULOS ===
from app.auth.routes import router as auth_router
from app.dashboard.routes import router as dashboard_router
from app.instagram.router import router as instagram_router
from app.ai.routes import router as ai_router

# Banco de dados
from app.database.session import get_db
from app.database.repositories.user_repo import UserRepository

# === INICIALIZA O FASTAPI ===
app = FastAPI(title="ProSolution API")

from app.database.base import init_db

@app.on_event("startup")
async def startup_event():
    await init_db()

# === ARQUIVOS ESTÁTICOS E TEMPLATES ===
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# === ROTA PRINCIPAL ===
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# === ROTEADORES (MÓDULOS) ===
app.include_router(auth_router, prefix="/auth")
app.include_router(dashboard_router)
app.include_router(instagram_router)
app.include_router(ai_router)

# === ROTEADORES DE BANCO / USERS ===
@app.get("/api")
async def root():
    return {"message": "🚀 ProSolution API running!"}

@app.get("/api/users")
async def list_users(db=Depends(get_db)):
    repo = UserRepository(db)
    return await repo.list_all()

@app.post("/api/users")
async def create_user(email: str, password_hash: str, db=Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.create({"email": email, "password_hash": password_hash})
    return user

from app.payments.routes import router as payments_router

app.include_router(payments_router)