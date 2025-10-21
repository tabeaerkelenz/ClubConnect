from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class ClubBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    country: Optional[str] = Field(None, max_length=4)
    city: Optional[str] = Field(None, max_length=128)
    sport: Optional[str] = Field(None, max_length=100)
    founded_year: Optional[int] = None
    description: Optional[str] = None


class ClubCreate(ClubBase):
    pass


class ClubUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    country: Optional[str] = Field(None, max_length=4)
    city: Optional[str] = Field(None, max_length=128)
    sport: Optional[str] = Field(None, max_length=100)
    founded_year: Optional[int] = None
    description: Optional[str] = None


class ClubRead(ClubBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
