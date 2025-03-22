# app/api/routers.py
from fastapi import APIRouter
from app.api.endpoints import (
    meeting_room_router,
    reservation_router,
    user_router,
)

main_router = APIRouter()

main_router.include_router(
    meeting_room_router, prefix="/api/meeting_rooms", tags=["Meeting Rooms"]
)
main_router.include_router(
    reservation_router, prefix="/api/reservations", tags=["Reservations"]
)
main_router.include_router(user_router)
