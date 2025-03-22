# app/core/user.py
from typing import Optional, Union

from fastapi import Depends, Request
from fastapi_users import (
    BaseUserManager,
    FastAPIUsers,
    IntegerIDMixin,
    InvalidPasswordException,
)
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_async_session
from app.models.user import User
from app.schemas.user import UserCreate


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


# Определяем транспорт. Передавать токен будем через заголовок
# HTTP-запроса Authentication: Bearer
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


# Хранить токен будем в виде JWT
def get_jwt_strategy() -> JWTStrategy:
    # Для генерации токена, передаём секретный ключи
    # и срок действия токена в секундах
    return JWTStrategy(secret=settings.secret_key, lifetime_seconds=3600)


# Создаём объект бэкенда аутентификации с выбранными параметрами
auth_backend = AuthenticationBackend(
    # Имя бекэнда должно быть уникальным
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    # Опишем свои условия валидации пароля
    async def validate_password(
        self, password: str, user: Union[UserCreate, User]
    ) -> None:
        if len(password) < 3:
            raise InvalidPasswordException(reason="Слишком короткий пароль")
        if user.email in password:
            raise InvalidPasswordException(
                reason="Email в пароле не лучшее решение!"
            )

    # Переопределим корутину для действия после успешной регистрации юзера
    async def on_after_register(
        self, user: User, request: Optional[Request] = None
    ):
        # Вместо print можно настроить отправку письма, например
        print(f"Пользователь {user.email} зарегистрирован!")


# Корутина возвращающая объект класса UserManager
async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


# Создадим объект FastAPIUsers для связи объекта UserManager
# и бэкенда аутентификации
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
