# app/crud/reservation.py
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, between, or_, select, delete, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Reservation


class CRUDReservation(CRUDBase):
    async def get_room_reservations_at_the_same_time(
        self,
        # Через * обозначим что все дальнейшие параметры должны передаваться по
        # ключу. И расположим параметры со значением по-умолчанию перед
        # значениями без параметра по-умолчанию
        *,
        from_reserve: datetime,
        to_reserve: datetime,
        meetingroom_id: int,
        # Опциональный параметр - id объекта бронирования
        reservation_id: Optional[int] = None,
        session: AsyncSession,
    ) -> list[Reservation]:

        select_stmt = select(Reservation).where(
            Reservation.meetingroom_id == meetingroom_id,
            or_(
                between(
                    from_reserve,
                    Reservation.from_reserve,
                    Reservation.to_reserve,
                ),
                between(
                    to_reserve,
                    Reservation.from_reserve,
                    Reservation.to_reserve,
                ),
                and_(
                    from_reserve <= Reservation.from_reserve,
                    to_reserve >= Reservation.to_reserve,
                ),
            ),
        )
        # Если передан id бронирования, то проверим условие
        if reservation_id is not None:
            select_stmt = select_stmt.where(Reservation.id != reservation_id)
        reservations = await session.execute(select_stmt)
        reservations = reservations.unique().scalars().all()
        return reservations

    async def get_user_reservations_at_the_same_time(
        self,
        # Через * обозначим что все дальнейшие параметры должны передаваться по
        # ключу. И расположим параметры со значением по-умолчанию перед
        # значениями без параметра по-умолчанию
        *,
        from_reserve: datetime,
        to_reserve: datetime,
        user_id: int,
        # Опциональный параметр - id объекта бронирования
        reservation_id: Optional[int] = None,
        session: AsyncSession,
    ) -> list[Reservation]:

        select_stmt = select(Reservation).where(
            Reservation.user_id == user_id,
            or_(
                between(
                    from_reserve,
                    Reservation.from_reserve,
                    Reservation.to_reserve,
                ),
                between(
                    to_reserve,
                    Reservation.from_reserve,
                    Reservation.to_reserve,
                ),
                and_(
                    from_reserve < Reservation.from_reserve,
                    to_reserve > Reservation.to_reserve,
                ),
            ),
        )
        # Если передан id бронирования, то проверим условие
        if reservation_id is not None:
            select_stmt = select_stmt.where(Reservation.id != reservation_id)
        reservations = await session.execute(select_stmt)
        reservations = reservations.unique().scalars().all()
        return reservations

    async def get_reservations_for_room(
        self, room_id: int, include_past: bool, session: AsyncSession
    ):
        if include_past:
            reservations = await session.execute(
                # Получим все объекты Reservation
                select(Reservation).where(
                    # где id равен запрашиваему room_id
                    Reservation.meetingroom_id == room_id,

                    Reservation.to_reserve < datetime.now()
                ).order_by(Reservation.from_reserve.desc())
            )
        else:
            reservations = await session.execute(
                # Получим все объекты Reservation
                select(Reservation).where(
                    # где id равен запрашиваему room_id
                    Reservation.meetingroom_id == room_id,
                    #  И время окончания бронирования больше текущего времени
                    Reservation.to_reserve >= datetime.now()
                ).order_by(Reservation.from_reserve)
            )
        reservations = reservations.unique().scalars().all()
        return reservations

    async def get_reservations_for_user(
        self, user_id: int, include_past: bool, session: AsyncSession,
    ):
        if include_past:
            reservations = await session.execute(
                select(Reservation).where(
                Reservation.user_id == user_id,
                    #  И время окончания бронирования больше текущего времени
                    Reservation.to_reserve < datetime.now()
                ).order_by(Reservation.from_reserve.desc())
            )
        else:
            reservations = await session.execute(
                select(Reservation).where(
                    Reservation.user_id == user_id,
                    #  И время окончания бронирования больше текущего времени
                    Reservation.to_reserve >= datetime.now()
                ).order_by(Reservation.from_reserve)
            )
        reservations = reservations.unique().scalars().all()
        return reservations

    async def get_reservations_interval_for_user_today(
            self, user_id: int,
            from_time: datetime,
            to_time: datetime,
            session: AsyncSession,
    ) -> tuple[datetime | None, datetime | None]:
        # Рассчитываем временные границы текущего дня

        # Выполняем запрос для получения агрегированных данных
        result = await session.execute(
            select(
                func.min(Reservation.from_reserve),
                func.max(Reservation.to_reserve)
            )
            .where(
                Reservation.user_id == user_id,
                Reservation.from_reserve >= from_time,
                Reservation.to_reserve < to_time
            )
        )

        # Извлекаем результат (одна строка с двумя значениями)
        row = result.all()[0]

        # Возвращаем (None, None) если данных нет, иначе (min, max)
        return (row[0], row[1]) if row else (None, None)

    async def get_reservations_interval_for_user_today_advanced(self,
                                                                user_id: int,
                                                                from_time: datetime,
                                                                session: AsyncSession):
        # Рассчитываем границы дня
        start_of_day = datetime.combine(from_time.date(), datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)

        # Определяем условия для бронирований, активных в течение дня
        overlaps_condition = and_(
            Reservation.from_reserv < end_of_day,
            Reservation.to_reserv > start_of_day
        )

        # Корректируем времена бронирований под границы дня
        adjusted_from = case(
            [
                (Reservation.from_reserv < start_of_day, start_of_day),
            ],
            else_=Reservation.from_reserv
        )

        adjusted_to = case(
            [
                (Reservation.to_reserv > end_of_day, end_of_day - timedelta(microseconds=1)),
            ],
            else_=Reservation.to_reserv
        )

        # Формируем запрос
        result = await session.execute(
            select(
                func.min(adjusted_from),
                func.max(adjusted_to)
            ).filter(
                Reservation.user_id == user_id,
                overlaps_condition
            )
        )
        return result.first()

    async def get_reservations_current(
        self, session: AsyncSession,
    ):
        reservations = await session.execute(
            select(Reservation).where(
                #  И время окончания бронирования больше текущего времени
                Reservation.to_reserve >= datetime.now(),
                Reservation.from_reserve <= datetime.now()
            ).order_by(Reservation.from_reserve.desc())
        )
        reservations = reservations.unique().scalars().all()
        return reservations

    async def remove_older(
            self,
            session: AsyncSession,
            days: int,
    ):
         await session.execute(
            delete(Reservation).where(
                    Reservation.to_reserve <= datetime.now() - timedelta(days=days),
            )
         )
         await session.commit()

reservation_crud = CRUDReservation(Reservation)
