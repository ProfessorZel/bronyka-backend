# app/schemas/group.py
from typing import List

from pydantic import BaseModel, Extra, Field

from app import models
from app.schemas.group_room_permissions import GroupRoomPermission

# Базовый класс, от которого будем наследоваться
class Group(BaseModel):
    name: str = Field(None, min_length=2, max_length=100)
    adGroupDN: str = Field(None, min_length=2, max_length=500)
    class Config:
        # Запрещает передавать параметры, которые не будут описаны в схеме
        extra = Extra.forbid
        orm_mode = True

    class Meta:
        orm_model = models.Group


class GroupCreated(Group):
    id: int

class GroupWithPerms(GroupCreated):
    permissions: List[GroupRoomPermission]

class GroupUpdateWithPerms(Group):
    permissions: List[GroupRoomPermission]

