# app/models/audit.py
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func, Column, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.db import Base
from app.models import User, MeetingRoom


class TimesheetSetting(Base):
    __tablename__ = "timesheet_settings"  # Ensure table name is defined

    spreadsheet_url: Mapped[str] = mapped_column(Text, nullable=False)
    worksheet: Mapped[str] = mapped_column(Text, nullable=False)
    with_service_account: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (UniqueConstraint('spreadsheet_url', 'worksheet', name='spreadsheet_worksheet_uc'),)

    def __repr__(self) -> str:
        user_info = self.user.fio if self.user else "Unknown"
        return f"{self.time} (user: '{user_info}') {self.description}"