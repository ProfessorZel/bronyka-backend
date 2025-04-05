# app/api/validators.py
from typing import Optional
from datetime import datetime, timedelta
from app.core.config import settings

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.meeting_room import meeting_room_crud
from app.crud.reservation import reservation_crud
from app.crud.user import user_crud
from app.models import MeetingRoom, Reservation, User



# Корутина, которая проверяет уникальность имени переговорной
async def check_name_duplicate(room_name: str, session: AsyncSession, previous_room_id: int = None, ) -> None:
    # и вторым параметром передаём сессию в CRUD функцию
    room_id = await meeting_room_crud.get_room_id_by_name(room_name, session)
    # Если такой объект уже есть в базе - вызвать ошибку
    if room_id is not None and room_id != previous_room_id:
        raise HTTPException(
            status_code=422,
            detail="Такая переговорная комната уже существует!",
        )


# Корутина, которая проверяет, существует ли объект в БД с таким ID
async def check_meeting_room_exists(
    meeting_room_id: int, session: AsyncSession
) -> MeetingRoom:
    # Получаем объект из БД по ID
    meeting_room = await meeting_room_crud.get(meeting_room_id, session)
    if meeting_room is None:
        raise HTTPException(status_code=404, detail="Переговорка не найдена")
    return meeting_room

# Корутина, которая проверяет, существует ли объект в БД с таким ID
async def check_user_exists(
    user_id: int, session: AsyncSession
) -> MeetingRoom:
    # Получаем объект из БД по ID
    user = await user_crud.get(obj_id=user_id, session=session)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


async def check_reservation_intersections(
        from_reserve: datetime,
        to_reserve: datetime,
        meetingroom_id: int,
        user_id: int,
        session: AsyncSession,
        reservation_id: Optional[int] = None,
) -> None:
    reservation = await reservation_crud.get_room_reservations_at_the_same_time(
        from_reserve = from_reserve,
        to_reserve=to_reserve,
        meetingroom_id=meetingroom_id,
        session=session,
        reservation_id=reservation_id
    )
    if reservation:
        raise HTTPException(status_code=422, detail="Двойное бронирование одной комнаты, уже есть бронь:"+str(reservation))

    reservation = await reservation_crud.get_user_reservations_at_the_same_time(
        from_reserve = from_reserve,
        to_reserve=to_reserve,
        user_id=user_id,
        session=session,
        reservation_id=reservation_id
    )
    if reservation:
        raise HTTPException(status_code=422, detail="Двойное бронирование одним человеком, уже есть бронь:"+str(reservation))



async def check_reservation_before_edit(
    reservation_id: int, session: AsyncSession, user: User
) -> Reservation:
    reservation = await reservation_crud.get(
        # Для лучшего понимания, можно передавать параметры по ключу
        obj_id=reservation_id,
        session=session,
    )
    if not reservation:
        raise HTTPException(status_code=404, detail="Бронь не найдена!")
    if reservation.user_id != user.id and not user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Невозможно редактировать или удалять чужую бронь!",
        )
    if reservation.to_reserve < datetime.now() and not user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Нельзя удалять/изменять бронь после ее завершения, это может сделать только Администратор",
        )
    if reservation.from_reserve < datetime.now() - timedelta(minutes = settings.deny_cancel_after_minutes_used) and not user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail=f"Нельзя удалять/изменять бронь через {settings.deny_cancel_after_minutes_used} минут после ее начала, это может сделать только Администратор",
        )
    return reservation
