# app/core/user.py
import logging
import secrets
import ssl
from typing import Optional, Union

from fastapi_users.db import BaseUserDatabase
from fastapi_users.password import PasswordHelperProtocol

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
from ldap3 import Server, Connection, ALL, Tls
from ldap3.core.exceptions import LDAPException
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
            return None

        # Пробуем аутентифицировать через LDAP
        user = await self.authenticate_with_ldap(credentials)
        return user

    async def authenticate_with_ldap(
            self, credentials: OAuth2PasswordRequestForm
    ) -> Optional[User]:
        """Аутентификация пользователя через LDAP"""
        username = credentials.username
        password = credentials.password

        logging.error(f"LDAP AUTH: Started for {username}")

        if not username or not password:
            logging.error("LDAP AUTH: No username or password")
            return None

        if settings.DEVELOPMENT_MODE:
            email, fio, group_dns = devmap_search(username, password)
        else:
            email, fio, group_dns = ldap_search_user(username, password)

        if email is None:
            logging.error("LDAP AUTH: Failed")
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
            user = await self.get_by_email(email)
        except UserNotExists:
            user = None

        if not user:
            user = await self.create(
                UserCreate(
                    email=email,
                    is_active=True,
                    is_superuser=False,
                    password=secrets.token_urlsafe(32),
                    fio=fio,
                )
            )

        if user.is_superuser != super_user or user.group_id != group_id:
            user = await self.update(UserUpdate(is_superuser=super_user, group_id=group_id, fio=fio), user, False)

        return user

def devmap_search(username, password: str) -> (str, str, list[str]):
    usermap = {
        "admin": {
            "password": "admin",
            "fio": "Admin Admin",
            "email": "admin@localhost.com",
            "groups": ["CN=admin,OU=groups,DC=example,DC=com",
                       "CN=group3,OU=groups,DC=example,DC=com"],
        },
        "group1": {
            "fio": "Group 1",
            "password": "group1",
            "email": "group1@localhost.com",
            "groups": ["CN=group1,OU=groups,DC=example,DC=com"],
        },
        "group2": {
            "fio": "Group 2",
            "password": "group2",
            "email": "group2@localhost.com",
            "groups": ["CN=group2,OU=groups,DC=example,DC=com"],
        }
    }
    if username not in usermap:
        return None, None, None
    user = usermap[username]
    if password != user["password"]:
        return None, None, None

    return user["email"], user["fio"], user["groups"]



def ldap_search_user(username, password: str) -> (str, str, list[str]):
    try:
        # поиск пользователя в AD для того чтобы получить DN
        tls_configuration = Tls(validate=ssl.CERT_REQUIRED) if settings.LDAP_USE_SSL else None
        server = Server(
            settings.LDAP_SERVER,
            port=settings.LDAP_PORT,
            use_ssl=settings.LDAP_USE_SSL,
            tls=tls_configuration,
            get_info=ALL
        )

        # Поиск пользователя в LDAP
        search_conn = Connection(
            server,
            user=settings.LDAP_BIND_DN,
            password=settings.LDAP_BIND_PASSWORD,
            auto_bind=True
        )

        search_filter = settings.LDAP_USER_SEARCH_FILTER.format(username=username)
        search_conn.search(
            search_base=settings.LDAP_USER_SEARCH_BASE,
            search_filter=search_filter,
            attributes=settings.LDAP_USER_ATTRIBUTES
        )

        if not search_conn.entries:
            logging.error("LDAP AUTH: No entries found")
            return None, None, None

        user_entry = search_conn.entries[0]
        user_dn = user_entry.entry_dn

        # Аутентификация пользователя
        auth_conn = Connection(server, user=user_dn, password=password)
        if not auth_conn.bind():
            logging.error("LDAP AUTH: Binding failed")
            return None, None, None
        # Извлечение данных пользователя
        email = getattr(user_entry, settings.LDAP_EMAIL_ATTRIBUTE, None).value
        fio = getattr(user_entry, settings.LDAP_FIO_ATTRIBUTE, None).value
        if not email:
            logging.error("LDAP AUTH: Email attribute not found")
            return None, None, None

        email = email + settings.LDAP_EMAIL_SUFFIX
        logging.error(f"LDAP AUTH: Email is '{email}'")

        if 'memberOf' in user_entry:
            group_dns = user_entry['memberOf'].value
        else:
            group_dns = []

        return email, fio, group_dns
    except LDAPException as e:
        print(f"LDAP error: {e}")
        logging.error(f"LDAP AUTH: {e}")
        return None, None, None
    finally:
        if 'search_conn' in locals() and search_conn.bound:
            search_conn.unbind()

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