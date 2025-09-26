from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    club_id: int
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=10, max_length=500)
    created_by_id: int
    created_at: datetime
    updated_at: datetime

class GroupCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=10, max_length=500)

class GroupUpdate(BaseModel):
    name: Optional[str] = Field(min_length=2, max_length=100)
    description: Optional[str] = Field(min_length=10, max_length=500)

