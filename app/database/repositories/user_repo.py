from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.database.models.user import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_data: dict) -> User:
        user = User(**user_data)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: str):
        result = await self.session.execute(select(User).filter_by(id=user_id))
        return result.scalars().first()

    async def get_by_email(self, email: str):
        result = await self.session.execute(select(User).filter_by(email=email))
        return result.scalars().first()

    async def list_all(self):
        result = await self.session.execute(select(User))
        return result.scalars().all()

    async def update(self, user_id: str, data: dict):
        await self.session.execute(update(User).where(User.id == user_id).values(**data))
        await self.session.commit()
        return await self.get_by_id(user_id)

    async def delete(self, user_id: str):
        await self.session.execute(delete(User).where(User.id == user_id))
        await self.session.commit()