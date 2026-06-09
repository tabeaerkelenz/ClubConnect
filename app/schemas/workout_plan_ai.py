from __future__ import annotations

from typing import List, Optional, Literal

from pydantic import BaseModel, Field, ConfigDict

from app.models.models import DayLabel


# ---------- Request ----------

class WorkoutPlanAIDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: str = Field(..., min_length=1, max_length=120)
    level: Optional[str] = Field(default=None, max_length=40)  # beginner/intermediate/advanced etc.
    duration_weeks: int = Field(..., ge=1, le=52)
    days_per_week: int = Field(..., ge=1, le=7)

    equipment: List[str] = Field(default_factory=list, max_length=20)
    constraints: List[str] = Field(default_factory=list, max_length=20)  # e.g. "knee friendly"
    notes: Optional[str] = Field(default=None, max_length=2000)

    # Optional: strict preference for naming / style
    style: Optional[Literal["simple", "detailed"]] = "simple"


# ---------- AI Output (validated JSON) ----------

class AIDraftExercise(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=10_000)

    sets: Optional[int] = Field(default=None, ge=1, le=20)
    repetitions: Optional[int] = Field(default=None, ge=1, le=100)

    rest_seconds: Optional[int] = Field(default=None, ge=0, le=600)
    tempo: Optional[str] = Field(default=None, max_length=32)
    weight_kg: Optional[int] = Field(default=None, ge=0, le=500)

    position: int = Field(..., ge=0, le=200)


class AIDraftItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    week_number: Optional[int] = Field(default=None, ge=1, le=52)
    day_label: Optional[DayLabel] = None
    order_index: int = Field(..., ge=0, le=200)
    title: Optional[str] = Field(default=None, max_length=120)

    exercises: List[AIDraftExercise] = Field(default_factory=list, max_length=50)


class WorkoutPlanAIDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=20_000)

    goal: Optional[str] = Field(default=None, max_length=120)
    level: Optional[str] = Field(default=None, max_length=40)
    duration_weeks: Optional[int] = Field(default=None, ge=1, le=52)

    items: List[AIDraftItem] = Field(default_factory=list, max_length=400)
