# app/schemas/user.py
from typing import Optional
from fastapi_users import schemas

from app.schemas.group import Group


class UserRead(schemas.BaseUser[int]):
    fio: Optional[str]
    group: Optional[Group]

class UserCreate(schemas.BaseUserCreate):
    fio: Optional[str]


class UserUpdate(schemas.BaseUserUpdate):
    fio: Optional[str]
    group_id: Optional[int]
