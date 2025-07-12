# app/api/endpoints/user.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.user import auth_backend, fastapi_users, current_user
from app.crud.user import user_crud
from app.schemas.user import UserRead, UserUpdate
from app.core.user import current_superuser

router = APIRouter()

router.include_router(
    # В роутере аутентификации передаётся объект
    # бэкенда аутентификации
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

users_router = fastapi_users.get_users_router(
    UserRead,
    UserUpdate,
)

# Модифицируем зависимости для каждого роута
for route in users_router.routes:
    if route.methods == {"GET"}:
        route.dependencies.append(Depends(current_user))
    else:
        route.dependencies.append(Depends(current_superuser))

router.include_router(
    users_router,
    prefix="/users",
    tags=["users"],
)

@router.get(
    "/users",
    response_model=list[UserRead],
    dependencies=[Depends(current_superuser)],
    # Добавим множество с полями, которые нужно исключить из ответа
    response_model_exclude={"password"},
    summary="Список пользователей",
    response_description="Запрос успешно получен",
    tags=["users"],
)
async def list_users(
    session: AsyncSession = Depends(get_async_session),
):
    users = await user_crud.get_multi(session=session)
    return users