from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.db.models import AttendanceStatus  # dein Enum

class AttendanceCreate(BaseModel):
    status: AttendanceStatus | None = None
    checked_in_at: datetime | None = None
    checked_out_at: datetime | None = None
    note: Optional[str] = None

class AttendanceUpdate(BaseModel):
    status: AttendanceStatus | None = None
    checked_in_at: datetime | None = None
    checked_out_at: datetime | None = None
    note: Optional[str] = None

class AttendanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: int
    user_id: int
    status: AttendanceStatus
    recorded_by_id: int | None = None
    checked_in_at: datetime | None = None
    checked_out_at: datetime | None = None
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
