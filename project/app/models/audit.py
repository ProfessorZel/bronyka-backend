# app/models/audit.py
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, func
from app.core.db import Base

class AuditEvent(Base):
    time = Column(DateTime, server_default=func.now())
    description = Column(Text(1000))
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)

    def __repr__(self) -> str:
        return f"{self.time} (user: {self.user_id}) {self.description}"
