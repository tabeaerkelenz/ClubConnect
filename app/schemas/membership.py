from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.db.models import MembershipRole


class MembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    club_id: int
    user_id: int
    role: MembershipRole


class MembershipCreate(BaseModel):
    email: EmailStr
    role: MembershipRole

    @field_validator("email")
    @classmethod
    def _norm_email(cls, v: str) -> str:
        return v.strip().lower()


class MembershipUpdate(BaseModel):
    role: MembershipRole
