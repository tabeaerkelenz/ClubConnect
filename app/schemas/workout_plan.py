from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.models import DayLabel


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class UTCBaseSchema(BaseModel):
    """
    - Pydantic v2
    - from_attributes=True
    - normalize timestamps to UTC
    """
    model_config = ConfigDict(from_attributes=True)

    @field_validator("created_at", "updated_at", mode="before", check_fields=False)
    @classmethod
    def _utc_datetimes(cls, v):
        if v is None:
            return v
        if isinstance(v, datetime):
            return _to_utc(v)
        return v


# ----------------------------
# WorkoutPlanExercise
# ----------------------------

class WorkoutPlanExerciseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=10_000)

    sets: Optional[int] = Field(default=None, ge=1)
    repetitions: Optional[int] = Field(default=None, ge=1)

    rest_seconds: Optional[int] = Field(default=None, ge=0)
    tempo: Optional[str] = Field(default=None, max_length=32)
    weight_kg: Optional[int] = Field(default=None, ge=0)

    position: int = Field(default=0, ge=0)


class WorkoutPlanExerciseCreate(WorkoutPlanExerciseBase):
    pass


class WorkoutPlanExerciseUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=10_000)

    sets: Optional[int] = Field(default=None, ge=1)
    repetitions: Optional[int] = Field(default=None, ge=1)

    rest_seconds: Optional[int] = Field(default=None, ge=0)
    tempo: Optional[str] = Field(default=None, max_length=32)
    weight_kg: Optional[int] = Field(default=None, ge=0)

    position: Optional[int] = Field(default=None, ge=0)


class WorkoutPlanExerciseRead(UTCBaseSchema, WorkoutPlanExerciseBase):
    id: int
    item_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ----------------------------
# WorkoutPlanItem
# ----------------------------

class WorkoutPlanItemBase(BaseModel):
    week_number: Optional[int] = Field(default=None, ge=1)
    day_label: Optional[DayLabel] = None
    order_index: int = Field(default=0, ge=0)
    title: Optional[str] = Field(default=None, max_length=120)


class WorkoutPlanItemCreate(WorkoutPlanItemBase):
    pass


class WorkoutPlanItemUpdate(BaseModel):
    week_number: Optional[int] = Field(default=None, ge=1)
    day_label: Optional[DayLabel] = None
    order_index: Optional[int] = Field(default=None, ge=0)
    title: Optional[str] = Field(default=None, max_length=120)


class WorkoutPlanItemRead(UTCBaseSchema, WorkoutPlanItemBase):
    id: int
    plan_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WorkoutPlanItemReadNested(WorkoutPlanItemRead):
    exercises: List[WorkoutPlanExerciseRead] = Field(default_factory=list)


# ----------------------------
# WorkoutPlan
# ----------------------------

class WorkoutPlanBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=20_000)

    goal: Optional[str] = Field(default=None, max_length=120)
    level: Optional[str] = Field(default=None, max_length=40)
    duration_weeks: Optional[int] = Field(default=None, ge=1)

    is_template: bool = False


class WorkoutPlanCreate(WorkoutPlanBase):
    pass


class WorkoutPlanUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=20_000)

    goal: Optional[str] = Field(default=None, max_length=120)
    level: Optional[str] = Field(default=None, max_length=40)
    duration_weeks: Optional[int] = Field(default=None, ge=1)

    is_template: Optional[bool] = None


class WorkoutPlanRead(UTCBaseSchema, WorkoutPlanBase):
    id: int
    club_id: int
    created_by_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WorkoutPlanReadNested(WorkoutPlanRead):
    items: List[WorkoutPlanItemReadNested] = Field(default_factory=list)
