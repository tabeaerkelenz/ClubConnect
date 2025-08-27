from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class ClubBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)

class ClubCreate(ClubBase):
    pass

class ClubUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)

class ClubRead(ClubBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config =  ConfigDict(from_attributes=True)
