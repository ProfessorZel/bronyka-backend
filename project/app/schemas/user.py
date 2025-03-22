# app/schemas/user.py
import datetime
from typing import Optional
from fastapi_users import schemas


class UserRead(schemas.BaseUser[int]):
    fio: Optional[str]
    birthdate: Optional[datetime.date]


class UserCreate(schemas.BaseUserCreate):
    fio: Optional[str]
    birthdate: Optional[datetime.date]


class UserUpdate(schemas.BaseUserUpdate):
    fio: Optional[str]
    birthdate: Optional[datetime.date]
