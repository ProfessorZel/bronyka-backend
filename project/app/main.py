# app/main.py
from fastapi import FastAPI
from app.core.config import settings

# Импортируем роутер
# и корутину для создания первого суперюзера
from app.api.routers import main_router
from app.core.init_db import create_first_superuser

app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version,
    redoc_url=None,
)

# Подключаем роутер
app.include_router(main_router)


@app.on_event("startup")
async def startup():
    await create_first_superuser()
