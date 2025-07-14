# app/core/config.py
import uuid
from typing import Optional

from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    app_title: str = "..."
    app_description: str = "..."
    database_url: str = "sqlite+aiosqlite:///./fastapi.db"
    app_version: str = "2.0.0"
    # приведет к разлогину при перезагрузке, но надежнее чем статический секрет
    secret_key: str = str(uuid.uuid4())
    first_superuser_email: Optional[str] = None
    first_superuser_password: Optional[str] = None
    deny_cancel_after_minutes_used: int = 10
    auth_token_lifetime_seconds:int = 86400
    backdate_reservation_allowed_seconds:int = 300
    max_reservation_duration_minutes:int = 1440

    # какой вид авторизации используется
    # LDAP - связь с доменом и авторизация через bind, но с созданием в локальной БД
    # DEVMAP - статический набор учеток для разработки, но с созданием в локальной БД
    # INTERNAL - авторизация по паролю из локальной БД
    AUTH_METHOD: str = "LDAP" # enum: LDAP, DEVMAP, INTERNAL

    # LDAP Configuration
    LDAP_SERVER: str = "example.com"
    LDAP_PORT: int = 389
    LDAP_USE_SSL: bool = False
    LDAP_BIND_DN: str = "CN=bind,DC=example,DC=com"
    LDAP_BIND_PASSWORD: str = "password"
    LDAP_USER_SEARCH_BASE: str = "DC=example,DC=com"
    LDAP_USER_SEARCH_FILTER: str = "(&(objectClass=person)(sAMAccountName={username}))"
    LDAP_USER_ATTRIBUTES: list = ["displayName", "sAMAccountName", "memberOf"]
    LDAP_LOGIN_ATTRIBUTE: str = "sAMAccountName"
    LDAP_FIO_ATTRIBUTE: str = "displayName"
    LDAP_ADMIN_GROUP: str = "CN=admins,DC=example,DC=com"

    class Config:
        env_file = ".env"

settings = Settings()
