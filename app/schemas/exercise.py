from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator, Field
from app.db.models import DayLabel

_MAX_NAME = 100
_MAX_DESCRIPTION = 1000


class ExerciseListParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    q: Optional[str] = None  # free-text search (optional)
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)


class ExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    plan_id: int
    name: str
    description: Optional[str] = None
    sets: Optional[int] = None
    repetitions: Optional[int] = None
    position: int
    day_label: Optional[DayLabel] = None


class ExerciseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    description: Optional[str] = None
    sets: Optional[int] = None
    repetitions: Optional[int] = None
    position: Optional[int] = None  # None = auto-append (max+1)
    day_label: Optional[DayLabel] = None

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        if len(v) > _MAX_NAME:
            raise ValueError(f"name cannot be longer than {_MAX_NAME} characters")
        return v

    @field_validator("description")
    @classmethod
    def _description(cls, v: str) -> str:
        if v is None:
            return v
        if len(v) > _MAX_DESCRIPTION:
            raise ValueError(
                f"description cannot be longer than {_MAX_DESCRIPTION} characters"
            )
        return v

    @field_validator("sets", "repetitions", "position")
    @classmethod
    def _not_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if v < 0:
            raise ValueError("Value must be positive")
        return v


class ExerciseUpdate(ExerciseCreate):
    name: Optional[str] = None
