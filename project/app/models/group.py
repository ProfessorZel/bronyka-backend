# app/models/meeting_room.py

from sqlalchemy import Column, String, Text
from app.core.db import Base
from sqlalchemy.orm import relationship


class Group(Base):
    # nullable = Значит, что не должно быть пустым
    name = Column(String(100), unique=True, nullable=False)
    adGroupDN = Column(Text(500), unique=True, nullable=False)

    #permissions = relationship("GroupRoomPermission", cascade="delete", lazy="joined")
    permissions = relationship(
        "GroupRoomPermission",
        back_populates="group",
        cascade="all, delete-orphan",  # Добавьте эту строку
        lazy = "joined",
        passive_deletes=True
    )
    def __repr__(self) -> str:
        return f"(id: {self.id}) {self.name} ({self.adGroupDN})"
