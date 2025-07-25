# app/schemas/group.py
from typing import List

from pydantic import BaseModel, Field

from app import models
from app.schemas.group_room_permissions import GroupRoomPermission, GroupRoomPermissionRepr


# Базовый класс, от которого будем наследоваться
class Group(BaseModel):
    name: str = Field(None, min_length=2, max_length=100)
    adGroupDN: str = Field(None, min_length=2, max_length=500)
    class Config:
        from_attributes = True

    class Meta:
        orm_model = models.Group


class GroupCreated(Group):
    id: int

class GroupWithPerms(GroupCreated):
    permissions: List[GroupRoomPermissionRepr]

class GroupUpdateWithPerms(Group):
    permissions: List[GroupRoomPermission]
