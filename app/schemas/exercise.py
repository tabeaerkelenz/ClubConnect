from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, field_validator, Field, model_validator
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
    from_template_id: int | None = None
    link_mode: Literal["snapshot", "linked"] | None = "snapshot"

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

    @model_validator(mode="after")
    def validate_choice(self):
        provided_core = any([self.name, self.description, self.sets, self.repetitions])
        if self.from_template_id and provided_core:
            raise ValueError("Provide either from_template_id or full fields, not both.")
        if not self.from_template_id and not provided_core:
            raise ValueError("Either from_template_id or full fields are required.")
        return self


class ExerciseUpdate(ExerciseCreate):
    name: Optional[str] = None
