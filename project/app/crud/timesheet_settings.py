# app/crud/reservation.py

from app.crud.base import CRUDBase
from app.models.timesheet_settings import TimesheetSetting


class CRUDTimesheetSettings(CRUDBase):
    pass

timesheet_setting_crud = CRUDTimesheetSettings(TimesheetSetting)
