# app/crud/reservation.py
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import User


class CRUDUser(CRUDBase):
    # Преобразуем функцию в методы класса
    async def get_user_by_email(
            # указываем параметр self, либо декоратор @staticmethod
            self,
            email: str,
            session: AsyncSession,
    ) -> Optional[User]:
        normalized_email = email.strip().lower()
        # Получаем объект класса Result
        db_user_id = await session.execute(
            select(User).where(
                func.lower(func.trim(User.email)) == normalized_email
            )
        )
        # Извлекаем из него конкретное значение
        db_user_id = db_user_id.scalars().first()
        return db_user_id

    async def get_user_by_fio(
            self,
            fio: str,
            session: AsyncSession,
    ) -> Sequence[User]:
        # Нормализуем входное значение: удаляем пробелы и приводим к нижнему регистру
        #normalized_fio = fio.strip().lower()
        # Сравниваем с нормализованными данными в БД
        db_user = await session.execute(
            select(User).where(
                User.fio == fio
            )
        )
        db_user = db_user.unique().scalars().all()
        return db_user
user_crud = CRUDUser(User)
