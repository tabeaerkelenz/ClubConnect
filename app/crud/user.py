from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.models import User, UserRole


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get a user by their email address (case insensitive)."""
    norm = email.strip().lower()
    stmt = select(User).where(User.email == norm)
    return db.execute(stmt).scalar_one_or_none()


# change identifier with email explicitly
def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Authenticate a user by their email and password."""
    user = get_user_by_email(db, email)
    if not user or not user.check_password(password):
        return None
    return user


def create_user(db: Session, *, name: str, email: str, password: str) -> User:
    """
    Create a user, set defaults to UserRole.athlete (public signup).
    """
    norm_email = str(email).strip().lower()

    if get_user_by_email(db, norm_email):
        raise ValueError("Email already registered")

    assigned_role = UserRole.athlete

    user = User(name=name, email=norm_email, role=assigned_role, is_active=True)
    user.password = password
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Email already registered")
    db.refresh(user)
    return user
