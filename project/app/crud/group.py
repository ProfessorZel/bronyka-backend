# app/crud/reservation.py
from typing import Union, Dict, Any

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Group, GroupRoomPermission
from app.schemas.group import GroupUpdateWithPerms


class CRUDGroup(CRUDBase):
    async def update(
            self,
            db_obj: Group,
            obj_in: Union[GroupUpdateWithPerms, Dict[str, Any]],
            session: AsyncSession
    ) -> Group:
        # Преобразование входных данных
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if "permissions" in update_data:

            permissions_data = update_data.pop("permissions")

            await session.execute(
                delete(GroupRoomPermission)
                .where(GroupRoomPermission.group_id == db_obj.id)
            )
            db_obj.permissions.clear()
            await session.flush()

            new_permissions = []
            for perm_data in permissions_data:
                new_perm = GroupRoomPermission(
                    max_future_reservation=perm_data["max_future_reservation"],
                    meetingroom_id=perm_data["meetingroom_id"],
                    group_id=db_obj.id  # Устанавливаем FK напрямую
                )
                new_permissions.append(new_perm)

            db_obj.permissions = new_permissions

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        # Явно загружаем связанные разрешения
        await session.refresh(db_obj, ["permissions"])

        return db_obj

group_crud = CRUDGroup(Group)
