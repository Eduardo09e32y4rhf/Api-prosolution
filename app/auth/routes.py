
from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.repositories.user_repo import UserRepository

router = APIRouter(tags=["Auth"])

@router.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    repo = UserRepository(db)
    user = await repo.get_by_email(email)

    if not user:
        raise HTTPException(status_code=401, detail="Usuário inválido")

    return RedirectResponse("/dashboard", status_code=302)
