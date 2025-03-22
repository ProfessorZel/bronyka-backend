# app/api/endpoints/meeting_room.py
from typing import List
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_async_session
from app.core.user import current_superuser
from app.crud.meeting_room import meeting_room_crud
from app.crud.reservation import reservation_crud
from app.api.validators import check_meeting_room_exists, check_name_duplicate
from app.schemas.reservation import ReservationRoomDB
from app.schemas.meeting_room import (
    MeetingRoomCreate,
    MeetingRoomDB,
    MeetingRoomUpdate,
)

router = APIRouter()


@router.post(
    "/",
    response_model=MeetingRoomDB,
    # Чтобы не показывать опциональные поля None, укажем параметр _exclude_none
    # Если надо не показывать все значения по-умолчанию - _exclude_default
    response_model_exclude_none=True,
    dependencies=[Depends(current_superuser)],
    summary="Регистрация новой переговорной комнаты",
    response_description="Успешная регистрация комнаты",
)
async def create_new_meeting_room(
    meeting_room: MeetingRoomCreate,
    # Указываем зависимость, предоставляющую объект сессии как параметр функции
    session: AsyncSession = Depends(get_async_session),
):
    """
    (Могут пользоваться только суперпользователи)
    Регистрация новой комнаты для переговоров:

    - **name** = Название комнаты
    - **description** = Описание комнаты
    """
    # Вызываем функцию проверки уникальности поля name
    await check_name_duplicate(meeting_room.name, session)
    # Вторым параметром передаём сессию в CRUD метод
    new_room = await meeting_room_crud.create(meeting_room, session)
    return new_room


@router.get(
    "/",
    response_model=List[MeetingRoomDB],
    response_model_exclude_none=True,
    summary="Получить список всех переговорных комнат",
    response_description="Список получен",
)
async def get_all_meeting_rooms(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Список комнат для переговоров:

    - **name** = Название комнаты
    - **description** = Описание комнаты
    """
    get_rooms = await meeting_room_crud.get_multi(session)
    return get_rooms


# Обновление объекта передаём PATH методом
@router.patch(
    "/{meeting_room_id}",
    response_model=MeetingRoomDB,
    response_model_exclude_none=True,
    dependencies=[Depends(current_superuser)],
    summary="Изменение переговорной комнаты",
    response_description="Успешное измение комнаты",
)
async def partially_update_meeting_room(
    *,
    # ID обновляемого объекта
    meeting_room_id: int = Path(
        ...,
        ge=0,
        title="ID переговорной комнаты",
        description="Любое положительное число",
    ),
    # JSON-данные, которые отправил пользователь
    obj_in: MeetingRoomUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """
    (Могут пользоваться только суперпользователи)
    Измение комнаты для переговоров:
    - **meeting_room_id** = ID комнаты на изменение
    - **name** = Название комнаты
    - **description** = Описание комнаты
    """
    meeting_room = await check_meeting_room_exists(meeting_room_id, session)
    if obj_in.name is not None:
        # Если в переданных данных, есть поле name
        # проверяем его на уникальность
        await check_name_duplicate(obj_in.name, session)

    # Когда проверки завершены - передаём в корутину
    # все необходимые для обновления данные
    meeting_room = await meeting_room_crud.update(
        meeting_room, obj_in, session
    )
    return meeting_room


# ручка для удаления объекта из БД
@router.delete(
    "/{meeting_room_id}",
    response_model=MeetingRoomDB,
    response_model_exclude_none=True,
    dependencies=[Depends(current_superuser)],
    summary="Удаление переговорной комнаты",
    response_description="Успешное удаление комнаты",
)
async def remove_meeting_room(
    meeting_room_id: int = Path(
        ...,
        ge=0,
        title="ID переговорной комнаты",
        description="Любое положительное число",
    ),
    session: AsyncSession = Depends(get_async_session),
):
    """
    (Могут пользоваться только суперпользователи)
    Удаление комнаты для переговоров:

    - **meeting_room_id** = ID комнаты для удаления
    """
    meeting_room = await check_meeting_room_exists(meeting_room_id, session)
    meeting_room = await meeting_room_crud.remove(meeting_room, session)
    return meeting_room


# ручка для получения списка зарезервированных объектов
@router.get(
    "/{meeting_room_id}/reservations",
    response_model=list[ReservationRoomDB],
    # Добавим множество с полями, которые нужно исключить из ответа
    response_model_exclude={"user_id"},
    summary="Время бронирования конкретной переговорной комнаты",
    response_description="Запрос успешно получен",
)
async def get_reservations_for_room(
    meeting_room_id: int = Path(
        ...,
        ge=0,
        title="ID переговорной комнаты",
        description="Любое положительное число",
    ),
    session: AsyncSession = Depends(get_async_session),
):
    await check_meeting_room_exists(meeting_room_id, session)
    reservations = await reservation_crud.get_future_reservations_for_room(
        room_id=meeting_room_id, session=session
    )
    return reservations
