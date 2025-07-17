# app/api/endpoints/reservation.py
from fastapi import APIRouter, Depends, Path
from fastapi import HTTPException
from fastapi_users.exceptions import UserNotExists
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validators import (
    check_meeting_room_exists,
    check_reservation_intersections,
    check_reservation_before_edit,
    check_user_exists, check_reservation_permissions, check_reservation_exist,
)
from app.core.db import get_async_session
from app.core.user import current_user, current_superuser, get_user_manager
from app.crud.audit import audit_crud
from app.crud.reservation import reservation_crud
from app.models import User
from app.schemas.audit import AuditCreate
from app.schemas.reservation import (
    ReservationRoomDB,
    ReservationRoomUpdate,
    ReservationRoomCreate,
)

router = APIRouter()


# у объекта Reservation нет опциональных полей, поэтому нет
# параметра response_model_exclude_none=True
@router.post(
    "/",
    response_model=ReservationRoomDB,
    summary="Зарезервировать комнату",
    response_description="Комната зарезервирована",
)
async def create_reservation(
    reservation: ReservationRoomCreate,
    session: AsyncSession = Depends(get_async_session),
    # Получаем текущего пользователя и сохраняем его в переменную user
    user: User = Depends(current_user),
):
    """
    Запрос на бронирование конкретной комнаты

    - **from_reserve** = Дата начала бронирования. Формата 2022-12-14T23:06
    - **to_reserve** = Дата окончания бронирования. Формата 2022-12-15T08:56
    - **meetingroom_id** = Целое число. ID переговорной комнаты
    - **user_id** = Опциональное поле. ID пользователя, для которого создается бронь.
      Если указано, то пользователь должен быть суперпользователем.
      Если не указано, то бронь создается для текущего пользователя.
    """
    meeting_room = await check_meeting_room_exists(reservation.meetingroom_id, session)

    # Определяем, для какого пользователя создаем бронь
    reservation_user = user
    if reservation.user_id is not None:
        # Проверяем, является ли текущий пользователь суперпользователем
        if not user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Только суперпользователь может создавать бронирования для других пользователей"
            )
        # Проверяем существование пользователя, для которого создаем бронь
        reservation_user = await check_user_exists(user_id=reservation.user_id, session=session)
    # cyclic but syncs both variables
    reservation.user_id = reservation_user.id

    if not user.is_superuser:
        await check_reservation_permissions(
            to_reserve=reservation.to_reserve,
            meetingroom=meeting_room,
            user=reservation_user,
            session=session
        )

    await check_reservation_intersections(
        # Т.к. Валидатор принимает **kwargs, аргументы нужно передать
        # с указанием ключей
        from_reserve=reservation.from_reserve,
        to_reserve=reservation.to_reserve,
        meetingroom_id=reservation.meetingroom_id,
        user_id=reservation_user.id,
        session=session
    )

    new_reservation = await reservation_crud.create(reservation, session)

    # создаем аудит
    event = AuditCreate(
        description="Создано бронирование: {0}".format(
            new_reservation
        ),
        user_id=user.id
    )
    await audit_crud.create(event, session)

    return new_reservation


@router.get(
    "/",
    response_model=list[ReservationRoomDB],
    summary="Получить список зарезервированных комнат",
    response_description="Список успешно получен",
    description="Получить список зарезервированных комнат",
)
async def get_all_reservation(
    current: bool = False,
    session: AsyncSession = Depends(get_async_session),
):
    if current:
        reservations = await reservation_crud.get_reservations_current(session)
    else:
        reservations = await reservation_crud.get_multi(session)
    return reservations


@router.delete(
    "/{reservation_id}",
    response_model=ReservationRoomDB,
    summary="Удалить резервирование комнаты",
    response_description="Запрос на удаление выполнен",
)
async def delete_reservation(
    reservation_id: int = Path(
        ...,
        ge=0,
        title="ID резервирования",
        description="Любое положительное число",
    ),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
):
    """
    Удаление резервирования комнаты:

    - **reservation_id** = ID резервирования для удаления
    """
    reservation = await check_reservation_before_edit(
        reservation_id, session, user
    )
    reservation = await reservation_crud.remove(reservation, session)

    # создаем аудит
    event = AuditCreate(
        description="Удалено бронирование: {0}".format(
            reservation
        ),
        user_id=user.id
    )
    await audit_crud.create(event, session)

    return reservation


@router.patch(
    "/{reservation_id}",
    response_model=ReservationRoomDB,
    summary="Изменение резервирования комнаты",
    response_description="Успешное изменение резервирования комнаты",
)
async def update_reservation(
    *,
    reservation_id: int = Path(
        ...,
        ge=0,
        title="ID резервирования",
        description="Любое положительное число",
    ),
    reservation_edit: ReservationRoomUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
    user_manager = Depends(get_user_manager),
):
    """
    Запрос на изменение резервирования комнаты

    - **from_reserve** = Дата начала бронирования. Формата 2022-12-14T23:06
    - **to_reserve** = Дата окончания бронирования. Формата 2022-12-15T08:56
    - **reservation_id** = Целое число. ID резервирования
    - **user_id** = Опциональное поле. ID пользователя, для которого изменяется бронь.
      Если указано, то пользователь должен быть суперпользователем.
      Если не указано, то бронь изменяется для текущего пользователя.
    """

    if reservation_edit.user_id is not None:
        raise HTTPException(
            status_code=501,
            detail="Редактирование не поддерживает смену пользователя"
        )

    # Проверяем, что объект бронирования уже существует
    reservation_before = await check_reservation_exist(
        reservation_id, session
    )

    if not user.is_superuser:
        await check_reservation_permissions(
            to_reserve=reservation_edit.to_reserve,
            meetingroom=reservation_before.meetingroom,
            user=reservation_before.user,
            session=session
        )

    # Проверяем, что нет пересечений с другими бронированиями
    await check_reservation_intersections(
        # Новое время бронирования, распаковываем на ключевые аргументы
        from_reserve=reservation_edit.from_reserve,
        to_reserve=reservation_edit.to_reserve,
        reservation_id=reservation_id,
        meetingroom_id=reservation_before.meetingroom_id,
        user_id=reservation_before.user_id,
        session=session,
    )

    reservation = await reservation_crud.update(
        db_obj=reservation_before, obj_in=reservation_edit, session=session
    )

    # создаем аудит
    event = AuditCreate(
        description="Изменено бронирование {0}, было: {1}, стало: {2}".format(
            reservation.id,
            reservation_before,
            reservation
        ),
        user_id=user.id
    )
    await audit_crud.create(event, session)

    return reservation


@router.get(
    "/my_reservations",
    response_model=list[ReservationRoomDB],
    # Добавим множество с полями, которые нужно исключить из ответа
    response_model_exclude={"user_id"},
)
async def get_my_reservations(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
    history: bool = False,
):
    """
    Показывает список всех бронирований переговорных комнат для текущего пользователя
    """
    reservations = await reservation_crud.get_reservations_for_user(
        user_id=user.id, session=session, include_past=history
    )
    return reservations

@router.get(
    "/for-user/{id}",
    response_model=list[ReservationRoomDB],
    dependencies=[Depends(current_superuser)],
    # Добавим множество с полями, которые нужно исключить из ответа
    response_model_exclude={"user_id"},
    summary="Бронирования для конкретного пользователя",
    response_description="Запрос успешно получен",
)
async def get_reservations_for_user(
    id: int = Path(
        ...,
        ge=0,
        title="ID пользователя",
        description="Любое положительное число",
    ),
    history: bool = False,
    session: AsyncSession = Depends(get_async_session),
):
    await check_user_exists(user_id=id, session=session)
    reservations = await reservation_crud.get_reservations_for_user(
        user_id=id, session=session, include_past=history
    )
    return reservations