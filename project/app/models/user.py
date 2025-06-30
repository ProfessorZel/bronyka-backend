# app/models/user.py
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    fio = Column(String, nullable=False)
    # Поле с указанием внешнего ключа пользователей
    group_id = Column(Integer, ForeignKey("group.id"))
    group = relationship("Group", viewonly=True, lazy="joined")

    def __repr__(self) -> str:
        return f"(id: {self.id}) {self.fio}"
