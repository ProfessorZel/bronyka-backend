# app/api/endpoints/reporter.py
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validators import check_meeting_room_exists_by_name, \
    check_user_exists_by_email
from app.core.db import get_async_session
from app.crud.activity import activity_crud
from app.models.activity import Activity
from app.schemas.reporter import Ping

router = APIRouter()

@router.post(
    "/ping",
    summary="Получает ping от компьютера",
    response_description="Созданная группа",
)
async def post_ping_event(
    ping: Ping,
    session: AsyncSession = Depends(get_async_session),
):
    logging.error(f"Ping: {ping}")
    meeting_room = await check_meeting_room_exists_by_name(ping.computer, session)
    user = await check_user_exists_by_email(ping.activeUser, session)
    await activity_crud.create(
        Activity(
            user_id=user.id,
            meetingroom_id=meeting_room.id,
            computer_time=ping.timestamp,
        ),
        session=session
    )

