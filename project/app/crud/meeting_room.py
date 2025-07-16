# app/crud/meeting_room.py
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models import GroupRoomPermission
from app.models.meeting_room import MeetingRoom


# Дополним CRUD класс, наследовав от CRUDBase
class CRUDMeetingRoom(CRUDBase):

    # Преобразуем функцию в методы класса
    async def get_room_id_by_name(
        # указываем параметр self, либо декоратор @staticmethod
        self,
        room_name: str,
        session: AsyncSession,
    ) -> Optional[int]:
        # Получаем объект класса Result
        db_room_id = await session.execute(
            select(MeetingRoom.id).where(MeetingRoom.name == room_name)
        )
        # Извлекаем из него конкретное значение
        db_room_id = db_room_id.scalars().first()
        return db_room_id

    async def get_allowed_rooms(self,
                                group_id: int,
                                session: AsyncSession) -> List[MeetingRoom]:
        room_list = await session.execute(
            select(MeetingRoom)
                .join(GroupRoomPermission,
                      GroupRoomPermission.meetingroom_id == MeetingRoom.id)
                .where(GroupRoomPermission.group_id == group_id)
        )
        room_list = room_list.unique().scalars().all()
        return room_list


# Объект CRUD наследуем уже не от CRUDBase, а от
# CRUDMeetingRoom, чтобы был доступен дополнительный
# метод get_room_id_by_name
meeting_room_crud = CRUDMeetingRoom(MeetingRoom)
