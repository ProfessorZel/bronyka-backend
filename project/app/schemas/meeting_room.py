# app/schemas/meeting_room.py

from typing import Optional
from pydantic import BaseModel, Field, validator, field_validator


# Базовый класс схемы, от которого наследуем все остальные
class MeetingRoom(BaseModel):
    name: str = Field(None, min_length=2, max_length=100)
    description: Optional[str]
    icon: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "name": "Переговорная комната #1",
                "description": "Просторная комната на 40 человек. ",
                "icon": "icon12.jpg",
            }
        }


# Теперь наследуем схему не от BaseModel а от MeetingRoom
class MeetingRoomCreate(MeetingRoom):
    @field_validator("name")
    def name_is_numeric(cls, value: str):
        if value.isnumeric():
            raise ValueError("Имя не может быть числом")
        return value


# Pydantic-схема, которая описывает объект из БД для валидации
class MeetingRoomDB(MeetingRoomCreate):
    id: int

    # Укажем FastAPI, что он может сериализовать объёкт базы данных
    # а не только словарь или json
    class Config:
        from_attributes = True


class MeetingRoomUpdate(MeetingRoom):
    @field_validator("name")
    def name_cannot_be_null(cls, value):
        if value is None:
            raise ValueError("Имя переговорки не может быть пустым")
        return value
