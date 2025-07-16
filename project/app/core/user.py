# app/core/user.py
import logging
import secrets
from typing import Optional, Union, Any

from fastapi_users.db import BaseUserDatabase
from fastapi_users.password import PasswordHelperProtocol

from app.core import authenticators, security
from app.core.authenticators.common import AuthType
from app.core.config import settings
from app.core.db import get_async_session
from app.crud.group import group_crud
from app.models.user import User
from app.schemas.group import Group
from app.schemas.user import UserCreate
from app.schemas.user import UserUpdate
from fastapi import Depends, Request
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
        if not settings.AUTH_REQURE_STRONGPASS:
            return

        if not security.check_password(password):
            raise InvalidPasswordException(reason="Не надежный пароль")

        if user.email in password:
            raise InvalidPasswordException(
                reason="Email в пароле не лучшее решение!"
            )

    async def authenticate(
            self, credentials: OAuth2PasswordRequestForm
    ) -> Optional[models.UP]:
        if settings.AUTH_METHOD == AuthType.INTERNAL:
            return await super().authenticate(credentials)

        if settings.AUTH_METHOD == AuthType.DEVMAP:
            login, fio, group_dns = authenticators.devmap_search(credentials)
        elif settings.AUTH_METHOD == AuthType.LDAP:
            login, fio, group_dns = authenticators.ldap_search(credentials)
        else:
            logging.error("AUTH: Unknown authentication method")
            return None

        if login is None:
            logging.warn("AUTH: Failed auth")
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
            try:
                # legacy mapping
                user = await self.get_by_email(login + settings.LDAP_EMAIL_SUFFIX)
                await self.update(UserUpdate(email=login), user, True)
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
        if not user.is_active:
            logging.warn("AUTH: Account disabled")
            return None

        if user.is_superuser != super_user or user.group_id != group_id:
            user = await self.update(UserUpdate(is_superuser=super_user, group_id=group_id), user, False)

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