# app/api/endpoints/reporter.py
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi_users.exceptions import UserNotExists
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validators import check_meeting_room_exists_by_name
from app.core.db import get_async_session
from app.core.user import UserManager, get_user_manager
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
    manager: UserManager = Depends(get_user_manager),
):
    logging.info(f"Ping: {ping}")
    meeting_room = await check_meeting_room_exists_by_name(ping.computer, session)
    try:
        user = await manager.get_by_email(ping.activeUser)
    except UserNotExists:
        raise HTTPException(status_code=404, detail=f"No such user: {ping.activeUser}")

    await activity_crud.create(
        Activity(
            user_id=user.id,
            meetingroom_id=meeting_room.id,
            computer_time=ping.timestamp,
        ),
        session=session
    )

