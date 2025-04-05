# app/main.py
import logging
import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Импортируем роутер
# и корутину для создания первого суперюзера
from app.api.routers import main_router
from app.core.config import settings
from app.core.init_db import create_first_superuser

app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version,
    redoc_url=None,
)

# Подключаем роутер
app.include_router(main_router)

app.mount("/assets", StaticFiles(directory="/usr/src/app/app/assets"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('/usr/src/app/app/index.html')

@app.on_event("startup")
async def startup():
    await create_first_superuser()
    await check_tz()

async def check_tz():
    logging.log(logging.WARN, f"Current time:{datetime.now()}; TimeZone: {os.environ['TZ']};")
    logging.log(logging.WARN, settings)