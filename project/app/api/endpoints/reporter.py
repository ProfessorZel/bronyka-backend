# app/api/endpoints/reporter.py
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.schemas.reporter import Ping

router = APIRouter()

# у объекта Reservation нет опциональных полей, поэтому нет
# параметра response_model_exclude_none=True
@router.post(
    "/ping",
    #response_model=GroupCreated,
    summary="Получает ping от компьютера",
    #dependencies=[Depends(current_superuser)],
    response_description="Созданная группа",
)
async def post_ping_event(
    ping: Ping,
    #session: AsyncSession = Depends(get_async_session),
    # Получаем текущего пользователя и сохраняем его в переменную user
    #user: User = Depends(current_user),
):
    logging.error(f"Ping: {ping}")