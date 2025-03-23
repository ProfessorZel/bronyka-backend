# app/crud/reservation.py
from typing import Optional
from datetime import datetime
from sqlalchemy import and_, between, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models import User, Reservation


class CRUDUser(CRUDBase):
    pass
user_crud = CRUDUser(User)
