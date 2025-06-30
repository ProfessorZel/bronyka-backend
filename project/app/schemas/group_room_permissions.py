# app/schemas/reservation.py
from datetime import timedelta

from pytimeparse.timeparse import timeparse

from pydantic import BaseModel, Extra, Field, validator

from app import models

# Базовый класс, от которого будем наследоваться
class GroupRoomPermission(BaseModel):
    max_future_reservation: timedelta = Field(...)
    meetingroom_id: int = Field(...)

    @validator("max_future_reservation", pre=True)
    def parse_duration(cls, v):
        if isinstance(v, timedelta):
            return v

        if isinstance(v, str):
            return timeparse(v)

        raise ValueError(v)

    class Config:
        # Запрещает передавать параметры, которые не будут описаны в схеме
        extra = Extra.forbid
        orm_mode = True

    class Meta:
        orm_model = models.GroupRoomPermission

