from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jose import jwt
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    token = request.cookies.get("token")
    if not token:
        return {"error": "Não autenticado"}

    data = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": data}
    )

