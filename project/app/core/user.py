# app/core/user.py
import logging
import secrets
from typing import Optional, Union, Any

from fastapi_users.db import BaseUserDatabase
from fastapi_users.password import PasswordHelperProtocol
from starlette import status

from app.core import authenticators
from app.core.config import settings
from app.core.db import get_async_session
from app.crud.group import group_crud
from app.models.user import User
from app.schemas.group import Group
from app.schemas.user import UserCreate
from app.schemas.user import UserUpdate
from fastapi import Depends, Request, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import (
    BaseUserManager,
    FastAPIUsers,
    IntegerIDMixin,
    InvalidPasswordException, models, )
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.exceptions import UserNotExists
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


# Определяем транспорт. Передавать токен будем через заголовок
# HTTP-запроса Authentication: Bearer
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


# Хранить токен будем в виде JWT
def get_jwt_strategy() -> JWTStrategy:
    # Для генерации токена, передаём секретный ключи
    # и срок действия токена в секундах
    return JWTStrategy(secret=settings.secret_key, lifetime_seconds=settings.auth_token_lifetime_seconds)


# Создаём объект бэкенда аутентификации с выбранными параметрами
auth_backend = AuthenticationBackend(
    # Имя бекэнда должно быть уникальным
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    session = None

    def __init__(self, user_db: BaseUserDatabase[models.UP, models.ID], session: AsyncSession,
                 password_helper: Optional[PasswordHelperProtocol] = None):
        super().__init__(user_db, password_helper)
        self.session = session

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

    async def authenticate(
            self, credentials: OAuth2PasswordRequestForm
    ) -> Optional[models.UP]:
        if credentials is None:
            logging.error("AUTH: No credentials")
            return None

        login = None
        if settings.AUTH_METHOD == "INTERNAL":
            return await super().authenticate(credentials)
        if settings.AUTH_METHOD == "DEVMAP":
            login, fio, group_dns = authenticators.devmap_search(credentials)
        elif settings.AUTH_METHOD == "LDAP":
            login, fio, group_dns = authenticators.ldap_search(credentials)

        if login is None:
            logging.error("AUTH: Failed")
            return None

        # теперь назначим права администратора и распределим по группам
        registered_groups = await group_crud.get_multi(self.session)
        super_user = False
        group_id = None

        for group_dn in group_dns:
            if super_user is False:
                if group_dn == settings.LDAP_ADMIN_GROUP:
                    super_user = True

            if group_id is None:
                for registered_group in registered_groups:
                    registered_group: Group = registered_group
                    if registered_group.adGroupDN == group_dn:
                        group_id = registered_group.id

            if super_user is True and group_id is not None:
                break

        # Поиск или создание пользователя в БД
        try:
            user = await self.get_by_email(login)
        except UserNotExists:
            user = await self.create(
                UserCreate(
                    email=login,
                    is_active=True,
                    is_superuser=False,
                    password=secrets.token_urlsafe(32),
                    fio=fio,
                )
            )

        if user.is_superuser != super_user or user.group_id != group_id:
            user = await self.update(UserUpdate(is_superuser=super_user, group_id=group_id, fio=fio), user, False)

        return user



# Корутина возвращающая объект класса UserManager
async def get_user_manager(user_db=Depends(get_user_db), session: AsyncSession = Depends(get_async_session)):
    yield UserManager(user_db, session)


# Создадим объект FastAPIUsers для связи объекта UserManager
# и бэкенда аутентификации
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)