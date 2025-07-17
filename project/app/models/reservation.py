# app/models/reservation.py

from sqlalchemy import DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.core.db import Base
from app.models import MeetingRoom, User


class Reservation(Base):
    __tablename__ = "reservation"

    # Corrected column definitions using Annotated style
    #id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_reserve: Mapped[DateTime] = mapped_column(DateTime)
    to_reserve: Mapped[DateTime] = mapped_column(DateTime)
    meetingroom_id: Mapped[int] = mapped_column(Integer, ForeignKey("meetingroom.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))

    # Corrected relationships with Mapped[]
    meetingroom: Mapped["MeetingRoom"] = relationship("MeetingRoom", viewonly=True, lazy="joined")
    user: Mapped["User"] = relationship("User", viewonly=True, lazy="joined")

    confirmed_activity: Mapped[Boolean] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"(id: {self.id}) компьютер '{self.meetingroom.name}' с {self.from_reserve} по {self.to_reserve} для пользователя '{self.user.fio}'"
