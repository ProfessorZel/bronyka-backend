# app/api/endpoints/__init__.py
from .meeting_room import router as meeting_room_router
from .reservation import router as reservation_router
from .user import router as user_router
from .audit import router as audit_router
from .files import router as files_router
from .group import router as group_router
from .activity import router as reporter_router
from .googlesheets import router as google_sheets_router
from .config import router as config_router
