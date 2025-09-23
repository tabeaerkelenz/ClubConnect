from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserRead(BaseModel):
    # v2 replacement for orm_mode
    model_config = ConfigDict(form_attributes=True)
    id: int
    name: str
    email: EmailStr
    is_active: bool


class PasswordChange(BaseModel):
    old_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)
