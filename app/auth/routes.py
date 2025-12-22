from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )

@router.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...)
):
    # autenticação real entra depois
    return RedirectResponse(
        url="/dashboard",
        status_code=302
    )