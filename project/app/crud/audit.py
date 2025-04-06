# app/crud/reservation.py

from datetime import datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.audit import AuditEvent


class CRUDAuditEvent(CRUDBase):
    async def remove_older(
            self,
            session: AsyncSession,
            days: int,
    ):
         await session.execute(
            delete(AuditEvent).where(
                    AuditEvent.time <= datetime.now() - timedelta(days=days),
            )
         )
         await session.execute(
            delete(AuditEvent).where(
                AuditEvent.time == None
            )
         )
         await session.commit()

audit_crud = CRUDAuditEvent(AuditEvent)






