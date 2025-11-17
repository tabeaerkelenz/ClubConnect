# app/repositories/user.py
from collections.abc import Mapping
from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.security import verify_password
from app.models.models import User

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.get(User, user_id)

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalar_one_or_none()

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Return the User if email+password are valid, otherwise None.
    NOTE: Caller decides what to do if user is inactive.
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def update_user_fields(db: Session, user: User, data: Mapping[str, Any]) -> User:
    for k, v in data.items():
        setattr(user, k, v)
    return user

def commit_and_refresh(db: Session, obj: Any) -> Any:
    db.commit()
    db.refresh(obj)
    return obj
