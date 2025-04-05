# app/crud/reservation.py

from datetime import datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.testing.assertsql import Or

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
                #  И время окончания бронирования больше текущего времени
                Or(
                    AuditEvent.time <= datetime.now() - timedelta(days=days),
                    AuditEvent.time == None
               )

            )
         )
         await session.commit()

audit_crud = CRUDAuditEvent(AuditEvent)






