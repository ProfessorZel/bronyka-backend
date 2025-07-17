# app/crud/activity.py
from datetime import timedelta
from typing import Any, Coroutine, Sequence

from sqlalchemy import select, Row, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import now

from app.crud.base import CRUDBase
from app.models import User
from app.models.activity import Activity


class CRUDActivity(CRUDBase):
    async def get_active_user_for_meeting_room(
            self,
            meetingroom_id: int,
            lookback_interval: timedelta,
            session: AsyncSession,
    ) -> User:
        pings = await session.execute(
            select(Activity).where(
                Activity.computer_time > now() - lookback_interval,
                Activity.meetingroom_id == meetingroom_id,
                Activity.user_id != None,
            ).order_by(Activity.computer_time.desc())
        )
        ping = pings.unique().scalars().first()
        return ping.user if ping else None

    async def get_latest_for_meeting_room(
            self,
            meetingroom_id: int,
            lookback_interval: timedelta,
            session: AsyncSession,
    ) -> Sequence[Activity]:
        pings = await session.execute(
            select(Activity).where(
                Activity.computer_time > now() - lookback_interval,
                Activity.meetingroom_id == meetingroom_id
            ).order_by(Activity.computer_time.desc())
        )
        ping = pings.unique().scalars().all()
        return ping
activity_crud = CRUDActivity(Activity)
