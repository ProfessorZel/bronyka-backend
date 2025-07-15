# app/api/routers.py
from fastapi import APIRouter
from app.api.endpoints import (
    meeting_room_router,
    reservation_router,
    user_router,
    audit_router,
    files_router,
    group_router,
    reporter_router,
    google_sheets_router,
    config_router
)

main_router = APIRouter()

main_router.include_router(
    meeting_room_router, prefix="/api/meeting_rooms", tags=["Meeting Rooms"]
)
main_router.include_router(
    reservation_router, prefix="/api/reservations", tags=["Reservations"]
)
main_router.include_router(user_router)

main_router.include_router(audit_router, prefix="/api/audit", tags=["Audit"])

main_router.include_router(files_router, prefix="/api/files", tags=["Files"])

main_router.include_router(group_router, prefix="/api/groups", tags=["Groups"])

main_router.include_router(reporter_router, prefix="/api/reporters", tags=["Reporters"])

main_router.include_router(google_sheets_router, prefix="/api/googlesheets", tags=["GoogleSheets"])

main_router.include_router(config_router, prefix="/api/config", tags=["Config"])