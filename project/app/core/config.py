# app/core/config.py
import secrets
import os
from enum import Enum

from pydantic.v1 import BaseSettings


class AuthType(Enum):
    INTERNAL = "INTERNAL"
    DEVMAP = "DEVMAP"
    LDAP = "LDAP"

class Settings(BaseSettings):
    app_title: str = "..."
    app_description: str = "..."
    database_url: str = "sqlite+aiosqlite:///./fastapi.db"
    app_version: str = "2.0.0"
    secret_key: str = None

    deny_cancel_after_minutes_used: int = 10
    auth_token_lifetime_seconds: int = 86400
    backdate_reservation_allowed_seconds: int = 300
    max_reservation_duration_minutes: int = 1440

    AUTH_METHOD: AuthType = AuthType.INTERNAL

    AUTH_REQURE_STRONGPASS: bool = True

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
    LDAP_EMAIL_SUFFIX: str = "@example.com"

    GOOGLE_SERVICE_ACCOUNT_FILE: str = "config/service_account_secret.json"

    class Config:
        env_file = ".env"


def get_or_create_secret_key() -> str:
    """Получает секретный ключ из файла или создает новый"""
    os.makedirs('config', exist_ok=True)
    key_file = 'config/secret_key.txt'

    if os.path.exists(key_file):
        with open(key_file, 'r') as f:
            return f.read().strip()
    else:
        new_key = secrets.token_urlsafe(32)
        with open(key_file, 'w') as f:
            f.write(new_key)
        return new_key

# Инициализация настроек
settings = Settings()

# Переопределение secret_key из файла
settings.secret_key = get_or_create_secret_key()