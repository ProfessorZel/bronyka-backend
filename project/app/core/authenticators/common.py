from typing import Any

from fastapi import HTTPException
from starlette import status

from app.core.config import settings


def auth_type_internal(
):
    async def current_user_dependency(*args: Any, **kwargs: Any):
        if settings.AUTH_METHOD != "INTERNAL":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail = f"Эта операция запрещена когда IdP равен {settings.AUTH_METHOD}")
        return None

    return current_user_dependency