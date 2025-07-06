# app/schemas/reservation.py
from datetime import timedelta
from typing import Any

from pytimeparse.timeparse import timeparse

from pydantic import BaseModel, Extra, Field, validator, field_serializer, field_validator

from app import models

# Базовый класс, от которого будем наследоваться
class GroupRoomPermission(BaseModel):
    max_future_reservation: timedelta = Field(...)
    meetingroom_id: int = Field(...)

    @field_validator("max_future_reservation", mode="before")
    @classmethod
    def parse_duration(cls, v: object) -> timedelta:
        if isinstance(v, int):
            return timedelta(seconds=v)

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


class GroupRoomPermissionRepr(GroupRoomPermission):
    @field_serializer('max_future_reservation')
    def serialize_duration(self, max_future_reservation: timedelta) -> str:
        return str(max_future_reservation)


