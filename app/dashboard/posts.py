"""Edição de posts: legenda, imagem, agendamento e exclusão."""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.csrf import verify_csrf
from app.core.images import InvalidImageError, process_image
from app.core.storage import new_image_key, storage
from app.core.templates import templates
from app.core.timeutils import local_to_utc, utc_to_local, utcnow
from app.database.models.post import Post
from app.database.models.user import User
from app.database.session import get_db
from app.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard/posts", tags=["Posts"], dependencies=[Depends(verify_csrf)])

CAPTION_MAX = 2200  # limite de legenda do Instagram
HASHTAGS_MAX = 30  # limite de hashtags por post
TITLE_MAX = 100
MIN_LEAD_TIME = timedelta(minutes=5)
LOCKED_STATUSES = {"publishing", "published"}
HASHTAG_RE = re.compile(r"#\w+")

# Mensagens por código: a URL carrega só o código, nunca texto livre
MESSAGES = {
    "saved": "Legenda salva.",
    "image_saved": "Imagem enviada.",
    "image_cropped": "Imagem enviada. Ajustamos o enquadramento para o formato aceito pelo Instagram.",
    "image_removed": "Imagem removida.",
    "unscheduled": "Agendamento cancelado. O post voltou para rascunho.",
}


async def _get_own_post(db: AsyncSession, user: User, post_id: int) -> Post:
    post = (await db.execute(select(Post).where(Post.id == post_id, Post.user_id == user.id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    return post


def validate_caption(title: str, content: str) -> str | None:
    """Devolve a mensagem de erro ou None se a legenda for válida."""
    if not title.strip():
        return "Dê um título ao post."
    if len(title.strip()) > TITLE_MAX:
        return f"O título pode ter no máximo {TITLE_MAX} caracteres."
    if not content.strip():
        return "A legenda não pode ficar vazia."
    if len(content) > CAPTION_MAX:
        return f"A legenda tem {len(content)} caracteres; o Instagram aceita no máximo {CAPTION_MAX}."
    hashtags = len(HASHTAG_RE.findall(content))
    if hashtags > HASHTAGS_MAX:
        return f"A legenda tem {hashtags} hashtags; o Instagram aceita no máximo {HASHTAGS_MAX}."
    return None


def _edit_context(post: Post, user: User, **extra: Any) -> dict[str, Any]:
    earliest = utc_to_local(utcnow() + MIN_LEAD_TIME).replace(tzinfo=None)
    scheduled_local = ""
    if post.scheduled_for:
        scheduled_local = utc_to_local(post.scheduled_for).strftime("%Y-%m-%dT%H:%M")
    return {
        "user": {"email": user.email, "name": user.display_name},
        "post": post,
        "locked": post.status in LOCKED_STATUSES,
        "caption_max": CAPTION_MAX,
        "hashtags_max": HASHTAGS_MAX,
        "max_upload_mb": settings.MAX_UPLOAD_MB,
        "scheduled_local": scheduled_local,
        "earliest_local": earliest.strftime("%Y-%m-%dT%H:%M"),
        "timezone": settings.APP_TIMEZONE,
        "active_menu": "create",
        **extra,
    }


def _render_edit(request: Request, user: User, post: Post, status_code: int = 200, **extra: Any) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "edit_post.html", _edit_context(post, user, **extra), status_code=status_code
    )


def _locked_response(request: Request, user: User, post: Post) -> HTMLResponse:
    return _render_edit(
        request,
        user,
        post,
        status_code=409,
        error="Este post já foi publicado (ou está sendo publicado) e não pode mais ser alterado.",
    )


async def _delete_image_quietly(key: str | None) -> None:
    """Apaga o arquivo antigo. Falhar aqui deixa lixo no armazenamento, mas nunca deve quebrar a ação do usuário."""
    if not key:
        return
    try:
        await storage.delete(key)
    except Exception:
        logger.exception("Não foi possível apagar a imagem %s do armazenamento", key)


@router.get("/{post_id}/edit", response_class=HTMLResponse)
async def edit_post_page(
    request: Request, post_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> HTMLResponse:
    post = await _get_own_post(db, user, post_id)
    code = request.query_params.get("msg", "")
    return _render_edit(request, user, post, message=MESSAGES.get(code))


@router.post("/{post_id}/edit", response_model=None)
async def edit_post(
    request: Request,
    post_id: int,
    title: str = Form(""),
    content: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse | RedirectResponse:
    post = await _get_own_post(db, user, post_id)
    if post.status in LOCKED_STATUSES:
        return _locked_response(request, user, post)

    error = validate_caption(title, content)
    if error:
        # Mantém o que o usuário digitou, sem gravar
        post.title, post.content = title, content
        db.expunge(post)
        return _render_edit(request, user, post, status_code=400, error=error)

    post.title = title.strip()
    post.content = content.strip()
    await db.commit()
    return RedirectResponse(f"/dashboard/posts/{post_id}/edit?msg=saved", status_code=303)


@router.post("/{post_id}/image", response_model=None)
async def upload_image(
    request: Request,
    post_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse | RedirectResponse:
    post = await _get_own_post(db, user, post_id)
    if post.status in LOCKED_STATUSES:
        return _locked_response(request, user, post)

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    raw = await file.read(max_bytes + 1)
    try:
        processed = await asyncio.to_thread(process_image, raw, max_bytes)
    except InvalidImageError as exc:
        return _render_edit(request, user, post, status_code=400, error=str(exc))

    new_key = new_image_key(user.id)
    old_key = post.image_key
    await storage.save(new_key, processed.data)
    post.image_key = new_key
    try:
        await db.commit()
    except Exception:
        await _delete_image_quietly(new_key)  # não deixa arquivo órfão se o banco falhar
        raise
    await _delete_image_quietly(old_key)

    code = "image_cropped" if processed.cropped else "image_saved"
    return RedirectResponse(f"/dashboard/posts/{post_id}/edit?msg={code}", status_code=303)


@router.post("/{post_id}/image/remove", response_model=None)
async def remove_image(
    request: Request, post_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> HTMLResponse | RedirectResponse:
    post = await _get_own_post(db, user, post_id)
    if post.status in LOCKED_STATUSES:
        return _locked_response(request, user, post)

    old_key = post.image_key
    post.image_key = None
    if post.status == "scheduled":
        # Sem imagem a publicação falharia: o agendamento é cancelado junto
        post.status = "draft"
        post.scheduled_for = None
    await db.commit()
    await _delete_image_quietly(old_key)
    return RedirectResponse(f"/dashboard/posts/{post_id}/edit?msg=image_removed", status_code=303)


@router.post("/{post_id}/schedule", response_model=None)
async def schedule_post(
    request: Request,
    post_id: int,
    scheduled_for: str = Form(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse | RedirectResponse:
    post = await _get_own_post(db, user, post_id)
    if post.status in LOCKED_STATUSES:
        return _locked_response(request, user, post)

    if not post.image_key:
        return _render_edit(
            request,
            user,
            post,
            status_code=400,
            error="Envie uma imagem antes de agendar: o Instagram não publica posts de feed sem imagem.",
        )
    if error := validate_caption(post.title, post.content):
        return _render_edit(request, user, post, status_code=400, error=error)

    try:
        # O navegador envia "YYYY-MM-DDTHH:MM" no horário local do usuário
        local_dt = datetime.strptime(scheduled_for, "%Y-%m-%dT%H:%M")
    except ValueError:
        return _render_edit(request, user, post, status_code=400, error="Data e hora inválidas.")

    when = local_to_utc(local_dt)
    if when < utcnow() + MIN_LEAD_TIME:
        return _render_edit(
            request, user, post, status_code=400, error="Escolha um horário pelo menos 5 minutos no futuro."
        )

    post.scheduled_for = when
    post.status = "scheduled"
    await db.commit()
    return RedirectResponse("/dashboard/calendar", status_code=303)


@router.post("/{post_id}/unschedule", response_model=None)
async def unschedule_post(
    request: Request, post_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> HTMLResponse | RedirectResponse:
    post = await _get_own_post(db, user, post_id)
    if post.status in LOCKED_STATUSES:
        return _locked_response(request, user, post)

    post.status = "draft"
    post.scheduled_for = None
    await db.commit()
    return RedirectResponse(f"/dashboard/posts/{post_id}/edit?msg=unscheduled", status_code=303)


@router.post("/{post_id}/delete")
async def delete_post(
    post_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    post = await _get_own_post(db, user, post_id)
    old_key = post.image_key
    await db.delete(post)
    await db.commit()
    await _delete_image_quietly(old_key)
    return RedirectResponse("/dashboard/create", status_code=303)
