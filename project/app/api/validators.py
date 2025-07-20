# app/api/validators.py
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.group import group_crud
from app.crud.meeting_room import meeting_room_crud
from app.crud.reservation import reservation_crud
from app.crud.timesheet_settings import timesheet_setting_crud
from app.crud.user import user_crud
from app.models import Group, TimesheetSetting
from app.models import GroupRoomPermission
from app.models import MeetingRoom, Reservation, User


# Корутина, которая проверяет уникальность имени переговорной
async def check_name_duplicate(room_name: str, session: AsyncSession, previous_room_id: int = None, ) -> None:
    # и вторым параметром передаём сессию в CRUD функцию
    room_id = await meeting_room_crud.get_room_by_name(room_name, session)
    # Если такой объект уже есть в базе - вызвать ошибку
    if room_id is not None and room_id.id != previous_room_id:
        raise HTTPException(
            status_code=422,
            detail="Такая переговорная комната уже существует!",
        )

# Корутина, которая проверяет, существует ли объект в БД с таким ID
async def check_meeting_room_exists_by_name(
    room_name: str, session: AsyncSession
) -> MeetingRoom:
    # Получаем объект из БД по ID
    meeting_room = await meeting_room_crud.get_room_by_name(room_name, session)
    if meeting_room is None:
        logging.warn(f"Unknown room name: {room_name}")
        raise HTTPException(status_code=404, detail=f"Переговорка не найдена: {room_name}")
    return meeting_room

# Корутина, которая проверяет, существует ли объект в БД с таким ID
async def check_meeting_room_exists(
    meeting_room_id: int, session: AsyncSession
) -> MeetingRoom:
    # Получаем объект из БД по ID
    meeting_room = await meeting_room_crud.get(meeting_room_id, session)
    if meeting_room is None:
        raise HTTPException(status_code=404, detail=f"Переговорка не найдена ID: {meeting_room_id}")
    return meeting_room

# Корутина, которая проверяет, существует ли объект в БД с таким ID
async def check_user_exists(
    user_id: int, session: AsyncSession
) -> User:
    # Получаем объект из БД по ID
    user = await user_crud.get(obj_id=user_id, session=session)
    if user is None:
        raise HTTPException(status_code=404, detail=f"Пользователь не найден ID: {user_id}")
    return user

# Корутина, которая проверяет, существует ли объект в БД с таким ID
async def check_group_exists(
    group_id: int, session: AsyncSession
) -> Group:
    # Получаем объект из БД по ID
    user = await group_crud.get(obj_id=group_id, session=session)
    if user is None:
        raise HTTPException(status_code=404, detail=f"Группа не найдена ID: {group_id}")
    return user

# Корутина, которая проверяет, существует ли объект в БД с таким ID
async def check_timesheet_setting_exists(
    timesheet_settings_id: int, session: AsyncSession
) -> TimesheetSetting:
    # Получаем объект из БД по ID
    timesheet_setting = await timesheet_setting_crud.get(obj_id=timesheet_settings_id, session=session)
    if timesheet_setting is None:
        raise HTTPException(status_code=404, detail=f"Timesheet с ID: {timesheet_settings_id}")
    return timesheet_setting



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

async def check_reservation_permissions(
        to_reserve: datetime,
        meetingroom: MeetingRoom,
        user: User,
        session: AsyncSession,
) -> None:
    group: Group = await group_crud.get(obj_id=user.group_id, session=session)
    if group is None:
        raise HTTPException(status_code=422, detail="Вам не назначена ни одна группа, бронирование запрещено.")

    perms = [perm for perm in group.permissions if perm.meetingroom_id == meetingroom.id]
    if len(perms) == 0:
        raise HTTPException(status_code=422,
                            detail=f"У группы {group.name} нет права на бронирование {meetingroom.name}")
    if len(perms) > 1:
        raise HTTPException(status_code=500, detail=f"Ошибка в данных, более 1 разрешения у одной группы {group.name} для {meetingroom.name}")
    perm: GroupRoomPermission = perms[0]

    if to_reserve - datetime.now() > perm.max_future_reservation:
        raise HTTPException(status_code=422,
                            detail=f"Группа {group.name} не может бронировать {meetingroom.name} больше чем на {perm.max_future_reservation} вперед")


async def check_reservation_exist(
    reservation_id: int, session: AsyncSession
) -> Reservation:
    reservation = await reservation_crud.get(
        # Для лучшего понимания, можно передавать параметры по ключу
        obj_id=reservation_id,
        session=session,
    )
    if not reservation:
        raise HTTPException(status_code=404, detail="Бронь не найдена!")

    return reservation

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
