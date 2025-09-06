from sqlalchemy.orm import Session
from ClubConnect.app.db.models import User
from ClubConnect.app.core.security import hash_password, verify_password

def get_user_by_email(db: Session, email: str) -> User | None:
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

def create_user(db: Session, *, name: str, email: str, password: str) -> User:
    if get_user_by_email(db, email):
        raise ValueError("Email already registered")
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
