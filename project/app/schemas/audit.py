# app/schemas/audit.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Extra, Field

from app.schemas.user import UserRead

TIME = (datetime.now()).isoformat(
    timespec="minutes"
)

# Базовый класс, от которого будем наследоваться
class AuditBase(BaseModel):
    time: datetime = Field(..., example=TIME)
    description: str = Field(..., example="description")
    user_id: Optional[int] = Field(
        None,
        description="ID пользователя выолнившего действие",
        example="1",
        nullable=True
    )
    user: Optional[UserRead] = Field(
        None,
        description="пользователь",
        nullable=True
    )
    class Config:
        # Запрещает передавать параметры, которые не будут описаны в схеме
        extra = Extra.forbid
        from_attributes = True

class AuditCreate(BaseModel):
    description: str
    user_id: Optional[int]
    class Config:
        # Запрещает передавать параметры, которые не будут описаны в схеме
        extra = Extra.forbid
