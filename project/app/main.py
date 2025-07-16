# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers import main_router
from app.core.config import settings
from app.timecard.job import run_fill_timecards


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    print("Starting lifespan")
    run_fill_timecards()
    yield
    # --- shutdown ---

app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version,
    redoc_url=None,
    lifespan=lifespan
)

# Подключаем роутер
app.include_router(main_router)

app.mount("/assets", StaticFiles(directory="/usr/src/app/app/assets"), name="static")
@app.get("/")
async def read_index():
    return FileResponse('/usr/src/app/app/index.html')


