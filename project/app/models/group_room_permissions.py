# app/models/group_room_permissions.py
from datetime import timedelta
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Interval, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.meeting_room import MeetingRoom
    from app.models.group import Group

class GroupRoomPermission(Base):
    __tablename__ = "grouproompermission"

    # Convert all columns to SQLAlchemy 2.x style
    id: Mapped[int] = mapped_column(primary_key=True)
    max_future_reservation: Mapped[timedelta] = mapped_column(Interval)

    meetingroom_id: Mapped[int] = mapped_column(Integer, ForeignKey("meetingroom.id"))
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("group.id", ondelete="CASCADE"))

    # Corrected relationships using Mapped[]
    meetingroom: Mapped["MeetingRoom"] = relationship("MeetingRoom", viewonly=True, lazy="joined")
    group: Mapped["Group"] = relationship("Group", back_populates="permissions")

    __table_args__ = (UniqueConstraint('group_id', 'meetingroom_id', name='_group_to_room_uc'),)

    def __repr__(self) -> str:
        return f"(id: {self.id}) {self.meetingroom.name} ({self.group.name})"
