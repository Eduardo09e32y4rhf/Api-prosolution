from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates

router = APIRouter(tags=["Legal"])


@router.get("/termos", response_class=HTMLResponse)
async def terms(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "legal/terms.html", {})


@router.get("/privacidade", response_class=HTMLResponse)
async def privacy(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "legal/privacy.html", {})


@router.get("/exclusao-de-dados", response_class=HTMLResponse)
async def data_deletion(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "legal/data_deletion.html", {})
