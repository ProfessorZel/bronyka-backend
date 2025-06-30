# app/api/endpoints/group.py
from fastapi import APIRouter, Depends, Path
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validators import (
    check_group_exists,
)
from app.core.db import get_async_session
from app.core.user import current_user, current_superuser
from app.crud.audit import audit_crud
from app.crud.group import group_crud
from app.models import User
from app.schemas.audit import AuditCreate
from app.schemas.group import (
    Group, GroupCreated, GroupWithPerms, GroupUpdateWithPerms,
)

router = APIRouter()


# у объекта Reservation нет опциональных полей, поэтому нет
# параметра response_model_exclude_none=True
@router.post(
    "/",
    response_model=GroupCreated,
    summary="Создать группу",
    dependencies=[Depends(current_superuser)],
    response_description="Созданная группа",
)
async def create_group(
    group: Group,
    session: AsyncSession = Depends(get_async_session),
    # Получаем текущего пользователя и сохраняем его в переменную user
    user: User = Depends(current_user),
):

    new_group = await group_crud.create(group, session)

    # создаем аудит
    event = AuditCreate(
        description="Создана группа: {0}".format(
            new_group
        )
    )
    await audit_crud.create(event, session, user)

    return new_group


@router.get(
    "/",
    response_model=list[GroupCreated],
    summary="Получить список всех групп",
    response_description="Список успешно получен",
    description="Получить список всех групп",
)
async def get_all_groups(
    session: AsyncSession = Depends(get_async_session),
):
    groups = await group_crud.get_multi(session)
    return groups


@router.delete(
    "/{group_id}",
    response_model=GroupCreated,
    dependencies=[Depends(current_superuser)],
    summary="Удалить группу",
    response_description="Запрос на удаление выполнен",
)
async def delete_group(
    group_id: int = Path(
        ...,
        ge=0,
        title="ID группыы",
        description="Любое положительное число",
    ),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
):

    group = await group_crud.get(
        # Для лучшего понимания, можно передавать параметры по ключу
        obj_id=group_id,
        session=session,
    )
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена!")
    group = await group_crud.remove(group, session)

    # создаем аудит
    event = AuditCreate(
        description="Удалена группа: {0}".format(
            group
        )
    )
    await audit_crud.create(event, session, user)

    return group


@router.patch(
    "/{group_id}",
    response_model=GroupWithPerms,
    summary="Изменение группу",
    response_description="Успешное изменение данных группы",
)
async def update_group(
    *,
    group_id: int = Path(
        ...,
        ge=0,
        title="ID группы",
        description="Любое положительное число",
    ),
    obj_in: GroupUpdateWithPerms,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
):
    group = await check_group_exists(group_id=group_id, session=session)

    # Проверка на дубликаты meetingroom_id
    meetingroom_ids = [perm.meetingroom_id for perm in obj_in.permissions]
    if len(meetingroom_ids) != len(set(meetingroom_ids)):
        duplicates = {x for x in meetingroom_ids if meetingroom_ids.count(x) > 1}
        raise HTTPException(
            status_code=400,
            detail=f"Обнаружены повторяющиеся meetingroom_id: {duplicates}. "
                   "Для каждой комнаты должно быть только одно разрешение."
        )

    updated_group = await group_crud.update(group, obj_in, session)

    # создаем аудит
    event = AuditCreate(
        description="Обновлена группа: {0}".format(
            updated_group
        )
    )
    await audit_crud.create(event, session, user)

    return updated_group


@router.get(
    "/{group_id}",
    response_model=GroupWithPerms,
    dependencies=[Depends(current_superuser)],

    summary="Данные группы",
    response_description="Запрос успешно получен",
)
async def get_group(
    group_id: int = Path(
        ...,
        ge=0,
        title="ID группы",
        description="Любое положительное число",
    ),
    session: AsyncSession = Depends(get_async_session),
):
    group = await check_group_exists(group_id=group_id, session=session)
    return group