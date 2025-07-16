# app/crud/reservation.py
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import User


class CRUDUser(CRUDBase):
    # Преобразуем функцию в методы класса
    async def get_user_by_email(
            # указываем параметр self, либо декоратор @staticmethod
            self,
            emal: str,
            session: AsyncSession,
    ) -> Optional[User]:
        # Получаем объект класса Result
        db_user_id = await session.execute(
            select(User).where(User.email == emal)
        )
        # Извлекаем из него конкретное значение
        db_user_id = db_user_id.scalars().first()
        return db_user_id
user_crud = CRUDUser(User)
