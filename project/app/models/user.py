# app/models/user.py
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import Column, DateTime, String
from app.core.db import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    fio = Column(String, nullable=False)
    birthdate = Column(DateTime)

    def __repr__(self) -> str:
        return f"(id: {self.id}) {self.fio}"
