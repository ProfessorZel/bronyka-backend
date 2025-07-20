# app/schemas/user.py
from pydantic import BaseModel


class FirstInit(BaseModel):
    login: str
    password: str