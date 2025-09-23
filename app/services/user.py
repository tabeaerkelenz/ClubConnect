from sqlalchemy.orm import Session
from app.crud.user import get_user_by_email, create_user


def create_user_service(db: Session, name: str, email: str, password: str):
    if get_user_by_email(db, email):
        raise ValueError("Email already registered")
    return create_user(db, name=name, email=email, password=password)
