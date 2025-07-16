# app/models/audit.py
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.db import Base
from app.models import User, MeetingRoom


class Activity(Base):
    __tablename__ = "activity_log"  # Ensure table name is defined

    #id: Mapped[int] = mapped_column(primary_key=True)
    received_at_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    computer_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    meetingroom_id: Mapped[int] = mapped_column(Integer, ForeignKey("meetingroom.id"))
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id"))

    # Corrected relationships with Mapped[]
    meetingroom: Mapped["MeetingRoom"] = relationship("MeetingRoom", viewonly=True, lazy="joined")
    user: Mapped[Optional["User"]] = relationship("User", viewonly=True, lazy="joined")
    def __repr__(self) -> str:
        user_info = self.user.fio if self.user else "Unknown"
        return f"{self.time} (user: '{user_info}') {self.description}"