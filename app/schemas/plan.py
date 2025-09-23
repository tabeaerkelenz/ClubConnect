from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator

from app.db.models import PlanType


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    plan_type: PlanType
    club_id: int
    description: Optional[str] = None  # made description optional
    created_by_id: int
    created_at: datetime
    updated_at: datetime


class PlanCreate(BaseModel):
    name: str
    plan_type: PlanType
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if not (1 <= len(v) <= 100):  # correct length to model length
            raise ValueError("name length 1..120")
        return v

    @field_validator("description")
    @classmethod
    def _desc(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 2000:
            raise ValueError("description max 2000")
        return v


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    plan_type: Optional[PlanType] = None
    description: Optional[str] = None
