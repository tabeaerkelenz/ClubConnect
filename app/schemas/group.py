from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    club_id: int
    name: str = Field(min_length=2, max_length=80)  # matches DB String(80)
    description: str | None = Field(default=None, min_length=10, max_length=500)
    created_by_id: int | None
    created_at: datetime
    updated_at: datetime


class GroupCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, min_length=10, max_length=500)


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    description: Optional[str] = Field(default=None, min_length=10, max_length=500)
