import logging

from fastapi import HTTPException
from starlette import status

from app.core.config import settings, AuthType


def auth_type_internal():
    if settings.AUTH_METHOD != AuthType.INTERNAL:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail = f"Эта операция запрещена когда IdP равен {settings.AUTH_METHOD}")
    return None