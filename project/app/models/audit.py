# app/models/audit.py
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.db import Base
from app.models import User


class AuditEvent(Base):
    __tablename__ = "auditevent"  # Ensure table name is defined

    # Convert all columns to SQLAlchemy 2.x style
    id: Mapped[int] = mapped_column(primary_key=True)
    time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    description: Mapped[str] = mapped_column(Text(1000))
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)

    # Corrected relationship using Mapped[]
    user: Mapped[Optional["User"]] = relationship("User", viewonly=True, lazy="joined")

    def __repr__(self) -> str:
        # Added safety check for missing user
        user_info = self.user.fio if self.user else "Unknown"
        return f"{self.time} (user: '{user_info}') {self.description}"