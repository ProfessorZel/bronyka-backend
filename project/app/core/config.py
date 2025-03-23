# app/core/config.py
import uuid
from typing import Optional
from pydantic import BaseSettings, EmailStr


class Settings(BaseSettings):
    app_title: str = "..."
    app_description: str = "..."
    database_url: str = "sqlite+aiosqlite:///./fastapi.db"
    app_version: str = "1.0.0"
    # приведет к разлогину при перезагрузке, но надежнее чем статический секрет
    secret_key: str = str(uuid.uuid4())
    first_superuser_email: Optional[EmailStr] = None
    first_superuser_password: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
