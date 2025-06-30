# app/models/group_room_permissions.py

from sqlalchemy import Column, ForeignKey, Integer, Interval, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.db import Base

class GroupRoomPermission(Base):
    max_future_reservation = Column(Interval)
    # Столбец с внешним ключом: ссылка на таблицу meetingroom
    meetingroom_id = Column(Integer, ForeignKey("meetingroom.id"))
    meetingroom: "MeetingRoom" = relationship("MeetingRoom", viewonly=True, lazy="joined")
    # Поле с указанием внешнего ключа пользователей
    group_id = Column(Integer, ForeignKey("group.id", ondelete="CASCADE"))
    group = relationship("Group", back_populates="permissions")

    __table_args__ = (UniqueConstraint('group_id', 'meetingroom_id', name='_group_to_room_uc'), )

    def __repr__(self) -> str:
        return f"(id: {self.id}) {self.meetingroom.name} ({self.group.name})"
