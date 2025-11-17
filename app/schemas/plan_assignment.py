from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.models import PlanAssigneeRole


class PlanAssigneeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: int
    plan_id: int
    user_id: int
    role: PlanAssigneeRole
    assigned_by_id: int
    created_at: datetime


class PlanAssigneeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: int
    role: PlanAssigneeRole
