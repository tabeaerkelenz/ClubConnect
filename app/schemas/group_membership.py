# app/schemas/group_membership.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional

class GroupMembershipCreate(BaseModel):
    user_id: int
    role: Optional[str] = "member"  # ggf. Enum

class GroupMembershipSet(BaseModel):  # für PUT /{user_id} (idempotent)
    role: Optional[str] = "member"

class GroupMembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    group_id: int
    user_id: int
    role: Optional[str] = None
    joined_at: datetime

class GroupMembershipInvite(BaseModel):
    email: EmailStr
    role: str | None = "member"
