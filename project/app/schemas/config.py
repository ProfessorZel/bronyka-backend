# app/schemas/user.py
from typing import Optional
from fastapi_users import schemas
from pydantic import BaseModel

from app.schemas.group import Group


class FirstInit(BaseModel):
    login: str
    password: str