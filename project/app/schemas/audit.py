# app/schemas/reservation.py
from typing import Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Extra, root_validator, validator, Field

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
    class Config:
        # Запрещает передавать параметры, которые не будут описаны в схеме
        extra = Extra.forbid
        orm_mode = True

class AuditCreate(BaseModel):
    description: str
    user_id: Optional[int]
    class Config:
        # Запрещает передавать параметры, которые не будут описаны в схеме
        extra = Extra.forbid
