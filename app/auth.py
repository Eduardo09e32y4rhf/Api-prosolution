from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User
from app.security import verify_password, create_token
from app.vpn_block import is_vpn

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    ip = request.client.host
    if is_vpn(ip):
        return {"error": "VPN/Proxy bloqueado"}

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        return {"error": "Credenciais inválidas"}

    token = create_token({
        "sub": user.email,
        "admin": user.is_admin,
        "plan": user.plan
    })

    resp = RedirectResponse("/dashboard", 302)
    resp.set_cookie("token", token, httponly=True)
    return resp
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
