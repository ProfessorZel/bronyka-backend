# app/schemas/user.py
from typing import Optional
from fastapi_users import schemas
from app.schemas.group import Group


class UserRead(schemas.BaseUser[int]):
    email: str
    fio: Optional[str]
    group: Optional[Group]

    class Config:
        from_attributes = True

class UserCreate(schemas.BaseUserCreate):
    email: str
    fio: Optional[str]

class UserUpdate(schemas.BaseUserUpdate):
    email: str
    fio: Optional[str]
    group_id: Optional[int]
