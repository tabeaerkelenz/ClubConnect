from typing import Optional

from pydantic import ValidationError, EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ClubConnect.app.db.models import User, UserRole
from ClubConnect.app.core.security import hash_password, verify_password

def get_user_by_email(db: Session, email: EmailStr) -> User | None:
    user = db.query(User).filter(User.email == email).first()   # type: ignore
    return user

def get_user_by_username(db: Session, username: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()     # type: ignore
    return user

def authenticate_user(db: Session, identifier: str, password: str) -> User | None:
    user = (db.query(User).filter(User.username == identifier).first()      # type: ignore
            or db.query(User).filter(User.email == identifier).first())     # type: ignore
    if not user or not verify_password(password, user.password_hash):
        return None
    return user

def create_user(db: Session, *, name: str, email: EmailStr, password: str, role: Optional[UserRole] = None) -> User:
    """
    Create a user. If role is not provided, defaults to UserRole.athlete (public signup).
    """
    if get_user_by_email(db, email):
        raise ValueError("Email already registered")

    assigned_role = role or UserRole.athlete

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=assigned_role,
        is_active=True
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Email already registered")
    db.refresh(user)
    return user
