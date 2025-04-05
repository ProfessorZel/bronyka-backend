# app/models/audit.py
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.models import User


class AuditEvent(Base):
    time = Column(DateTime, server_default=func.now())
    description = Column(Text(1000))
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    user: "User" = relationship("User", viewonly=True, lazy="joined")

    def __repr__(self) -> str:
        return f"{self.time} (user: '{self.user.fio}') {self.description}"
