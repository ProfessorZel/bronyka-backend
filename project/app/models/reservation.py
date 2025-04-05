# app/models/reservation.py
from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.models import MeetingRoom, User


class Reservation(Base):
    from_reserve = Column(DateTime)
    to_reserve = Column(DateTime)
    # Столбец с внешним ключом: ссылка на таблицу meetingroom
    meetingroom_id = Column(Integer, ForeignKey("meetingroom.id"))
    meetingroom: "MeetingRoom" = relationship("MeetingRoom", viewonly=True, lazy="joined")
    # Поле с указанием внешнего ключа пользователей
    user_id = Column(Integer, ForeignKey("user.id"))
    user: "User" = relationship("User", viewonly=True, lazy="joined")

    def __repr__(self) -> str:
        return f"(id: {self.id}) компьютер '{self.meetingroom.name}' с {self.from_reserve} по {self.to_reserve} для пользователя '{self.user.fio}'"
