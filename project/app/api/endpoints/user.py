# app/api/endpoints/user.py
from fastapi import APIRouter, Depends
from app.core.user import auth_backend, fastapi_users
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.core.user import current_superuser, current_user
from app.models import User

router = APIRouter()

router.include_router(
    # В роутере аутентификации передаётся объект
    # бэкенда аутентификации
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
    dependencies=[Depends(current_superuser)],
)



users_router = fastapi_users.get_users_router(
    UserRead,
    UserUpdate,
)

# Модифицируем зависимости для каждого роута
for route in users_router.routes:
    if route.methods == {"GET"}:
        route.dependencies = [Depends(current_user)]
    else:
        route.dependencies = [Depends(current_superuser)]

router.include_router(
    users_router,
    prefix="/users",
    tags=["users"],
)