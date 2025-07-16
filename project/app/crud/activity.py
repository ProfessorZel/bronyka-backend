# app/crud/reservation.py
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import User
from app.models.activity import Activity


class CRUDActivity(CRUDBase):
    pass
activity_crud = CRUDActivity(Activity)
