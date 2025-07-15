# app/api/endpoints/config.py.py
import secrets

from fastapi import APIRouter, Depends, HTTPException
from fastapi_users.exceptions import UserNotExists
from starlette import status

from app.core import security
from app.core.authenticators.common import auth_type_internal
from app.core.user import UserManager, get_user_manager
from app.schemas.config import FirstInit
from app.schemas.user import UserCreate

router = APIRouter()


@router.get(
    "/init",
    response_model=FirstInit,
    dependencies=[Depends(auth_type_internal)],
    summary="Первичный init конфига",
    response_description="Метод предназначен для настройки пользователя",
)
async def init_config(
    usermanager: UserManager = Depends(get_user_manager),
):
    login = "admin"
    try:
        await usermanager.get_by_email(login)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Инициализация уже произведена, если нужно повторить процедуру, то удалите файл fastapi.db (ЭТО УДАЛИТ ВСЕ ДАННЫЕ!) и перезапустите контейнер.")
    except UserNotExists:
        password = secrets.token_urlsafe(16)
        i = 0
        while not security.check_password(password=password):
            password = secrets.token_urlsafe(16)
            i += 1
            if i > 10:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="Невозможно создать надежный пароль, попробуйте снова")

        await usermanager.create(
            UserCreate(
                email=login,
                password=password,
                fio="Internal Admin",
                is_superuser=True,
            ),
            safe=False,
        )
        return FirstInit(
            login=login,
            password=password
        )