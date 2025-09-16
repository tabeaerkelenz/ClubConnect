from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator, field_serializer

# limits for MVP; adjust if UI needs different caps
_MAX_LOCATION = 100
_MAX_NOTE = 1000


# ––––– READ –––––
class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    starts_at: datetime
    ends_at: datetime
    location: str
    note: Optional[str] = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    # for standardize timestamps
    @field_serializer("starts_at", "ends_at", "created_at", "updated_at", when_used="json")
    def _to_utc_z(self, dt: datetime) -> str:
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# ––––––– WRITE ––––––––
class SessionCreate(BaseModel):
    starts_at: datetime
    ends_at: datetime
    location: str
    note: Optional[str] = None

    @field_validator("location")
    @classmethod
    def _trim_location(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("location must not be empty")
        if len(v) > _MAX_LOCATION:
            raise ValueError(f"location exceeds max length ({_MAX_LOCATION})")
        return v

    @field_validator("note")
    @classmethod
    def _trim_note(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) > _MAX_NOTE:
            raise ValueError(f"note exceeds max length ({_MAX_NOTE})")
        return v or None

    @model_validator(mode="after")
    def _time_order_and_tz(self) -> "SessionCreate":
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("starts_at and ends_at must be timezone-aware")
        if self.starts_at >= self.ends_at:
            raise ValueError("starts_at must be before ends_at")
        return self


class SessionUpdate(BaseModel):
    # partial update; server-side will use exclude_unset=True
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    location: Optional[str] = None
    note: Optional[str] = None

    @field_validator("location")
    @classmethod
    def _trim_location(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("location must not be empty")
        if len(v) > _MAX_LOCATION:
            raise ValueError(f"location exceeds max length ({_MAX_LOCATION})")
        return v

    @field_validator("note")
    @classmethod
    def _trim_note(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) > _MAX_NOTE:
            raise ValueError(f"note exceeds max length ({_MAX_NOTE})")
        return v or None

    @model_validator(mode="after")
    def _time_order_and_tz(self) -> "SessionUpdate":
        # Validate only if both provided; each must be tz-aware if present
        if self.starts_at is not None and self.starts_at.tzinfo is None:
            raise ValueError("starts_at must be timezone-aware")
        if self.ends_at is not None and self.ends_at.tzinfo is None:
            raise ValueError("ends_at must be timezone-aware")
        if self.starts_at is not None and self.ends_at is not None:
            if self.starts_at >= self.ends_at:
                raise ValueError("starts_at must be before ends_at")
        return self
