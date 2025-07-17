# app/api/endpoints/reporter.py
import logging
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi_users.exceptions import UserNotExists
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validators import check_meeting_room_exists_by_name
from app.core.db import get_async_session
from app.core.user import UserManager, get_user_manager, current_superuser
from app.crud.activity import activity_crud
from app.models.activity import Activity
from app.schemas.reporter import Ping

router = APIRouter()

@router.post(
    "/ping",
    summary="Получает ping от компьютера",
)
async def post_ping_event(
    ping: Ping,
    session: AsyncSession = Depends(get_async_session),
    manager: UserManager = Depends(get_user_manager),
):
    logging.info(f"Ping: {ping}")
    meeting_room = await check_meeting_room_exists_by_name(ping.computer, session)
    user = None
    if ping.activeUser is not None:
        try:
            user = await manager.get_by_email(ping.activeUser)
        except UserNotExists:
            logging.info(f"User {ping.activeUser} not found.")
            raise HTTPException(status_code=404, detail=f"No such user: {ping.activeUser}")

    await activity_crud.create(
        Activity(
            user_id=user.id if user else None,
            meetingroom_id=meeting_room.id,
            computer_time=ping.timestamp,
        ),
        session=session
    )

@router.get(
    "/",
    summary="Список пингов",
    response_model=List[Ping],
    response_description="Список пингов",
    dependencies=[Depends(current_superuser)],
)
async def list_reports(
    meetingroom_id: int = None,
    lookback: timedelta = timedelta(minutes=5),
    session: AsyncSession = Depends(get_async_session),
):
    if meetingroom_id is None:
        ping_list = await activity_crud.get(session)
    else:
        ping_list = await activity_crud.get_active_user_for_meeting_room(
            meetingroom_id=meetingroom_id,
            lookback_interval=lookback,
            session=session)
    pings = []
    for ping in ping_list:
        pings.append(Ping(
                timestamp=ping.computer_time,
                computer=ping.meetingroom.name,
                activeUser=ping.user.fio if ping.user else None,
                eventType=str(ping.received_at_time)
            )
        )
    return pings


