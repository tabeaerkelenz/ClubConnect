from typing import Optional

from pydantic import ValidationError, EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ClubConnect.app.db.models import User, UserRole
from ClubConnect.app.core.security import hash_password, verify_password

def get_user_by_email(db: Session, email: str) -> User | None:
    norm = email.strip().lower()        # normalize mail before comparison
    user = db.query(User).filter(User.email == norm).first()   # type: ignore
    return user

def authenticate_user(db: Session, email: str, password: str) -> User | None:       # change identifier with email explicitly
    user = get_user_by_email(db, email)
    if not user or not user.check_password(password):
        return None
    return user

def create_user(db: Session, *, name: str, email: str, password: str, role: Optional[UserRole] = None) -> User:
    """
    Create a user, set defaults to UserRole.athlete (public signup).
    """
    norm_email = str(email).strip().lower()

    if get_user_by_email(db, norm_email):
        raise ValueError("Email already registered")

    assigned_role = UserRole.athlete

    user = User(
        name=name,
        email=norm_email,
        role=assigned_role,
        is_active=True
    )
    user.password = password
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Email already registered")
    db.refresh(user)
    return user
