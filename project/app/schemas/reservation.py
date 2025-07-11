# app/schemas/reservation.py
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Extra, root_validator, validator, Field, field_validator, model_validator

from app.core.config import settings
from app.schemas.meeting_room import MeetingRoomDB
from app.schemas.user import UserRead

FROM_TIME = (datetime.now() + timedelta(minutes=10)).isoformat(
    timespec="minutes"
)
TO_TIME = (datetime.now() + timedelta(hours=10)).isoformat(timespec="minutes")


# Базовый класс, от которого будем наследоваться
class ReservationRoomBase(BaseModel):
    from_reserve: datetime = Field(..., example=FROM_TIME)
    to_reserve: datetime = Field(..., example=TO_TIME)
    user_id: Optional[str] = Field(
        None,
        description="ID пользователя, для которого создается бронь",
        example="1",
        nullable=True
    )

    class Config:
        # Запрещает передавать параметры, которые не будут описаны в схеме
        extra = Extra.forbid


class ReservationRoomUpdate(ReservationRoomBase):
    @field_validator("from_reserve")
    def check_from_reserve_later_than_now(cls, value):
        if value <= datetime.now() - timedelta(seconds=settings.backdate_reservation_allowed_seconds):
            raise ValueError(
                "Время начала бронирования не "
                "может быть меньше текущего времени"
            )
        return value

    @field_validator("user_id")
    def check_user_id_not_empty(cls, value):
        if value is not None and value.strip() == "":
            raise ValueError("Пользователь на которого назначают бронь не может быть пустым")
        return value

    @model_validator()
    def check_from_reserve_before_to_reserve(cls, values):
        if values["from_reserve"] >= values["to_reserve"]:
            raise ValueError(
                "Время начала бронирования, "
                "не может быть больше его окончания"
            )
        if values["to_reserve"] - values["from_reserve"] > timedelta(minutes=settings.max_reservation_duration_minutes):
            raise ValueError(
                f"Бронирование не может быть дольше {settings.max_reservation_duration_minutes} минут"
            )
        return values

    def __repr__(self) -> str:
        return f"(id: {self.id}) тот-же компьютер с {self.from_reserve} по {self.to_reserve} для пользователя {self.user_id} "


# наследуемся от ReservationRoomUpdate с его валидаторами
class ReservationRoomCreate(ReservationRoomUpdate):
    meetingroom_id: int


# Pydantic-схема для валидации объектов из БД
# но нельзя наследоваться от ReservationRoomCreate, т.к. унаследуется и валидаторы
# и при получении старых объектов из БД, у нас будет ошибка валидации по дате:
# старые записи по дате будут уже меньше текущей даты
class ReservationRoomDB(ReservationRoomBase):
    id: int
    meetingroom_id: int
    meetingroom: Optional[MeetingRoomDB]
    user_id: Optional[int]
    user: Optional[UserRead] = Field(
        None,
        description="пользователь",
        nullable=True
    )

    # разрешим сериализацию объектов из БД
    class Config:
        orm_mode = True
