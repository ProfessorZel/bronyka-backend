# app/schemas/reporter.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class Ping(BaseModel):
    timestamp: datetime
    computer: str
    activeUser: Optional[str] = None
    idleTime: Optional[float] = None