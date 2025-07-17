# app/crud/reservation.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.timesheet_settings import TimesheetSetting


class CRUDTimesheetSettings(CRUDBase):
    async def get_enabled(
            self, session: AsyncSession,
    ):
        reservations = await session.execute(
            select(TimesheetSetting).where(
               TimesheetSetting.is_enabled == True,
            )
        )
        reservations = reservations.unique().scalars().all()
        return reservations

timesheet_setting_crud = CRUDTimesheetSettings(TimesheetSetting)
