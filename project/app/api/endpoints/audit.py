# app/api/endpoints/user.py
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.user import current_superuser
from app.crud.audit import audit_crud
from app.schemas.audit import AuditBase

router = APIRouter()

@router.get(
    "/events",
    response_model=List[AuditBase],
    dependencies=[Depends(current_superuser)],
    summary="Аудит системы",
    response_description="Запрос успешно получен",
    tags=["audit"],
)
async def list_audit_events(
    session: AsyncSession = Depends(get_async_session),
):
    events = await audit_crud.get_multi(session=session)
    return events

@router.post(
    "/clear_old",
    dependencies=[Depends(current_superuser)],
    summary="Очистка старых событий системы",
    response_description="Запрос успешно получен",
    tags=["audit"],
)
async def list_audit_events(
    session: AsyncSession = Depends(get_async_session),
        days_after: int = 45
):
    await audit_crud.remove_older(session=session, days=days_after)