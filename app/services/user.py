from typing import Mapping, Any
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.user import get_user_by_email, update_user_fields, commit_and_refresh
from app.models.models import User
from app.exceptions.base import EmailExistsError
from app.schemas.user import UserUpdate

FORBIDDEN_FIELDS = {"is_active", "role", "password", "password_hash", "id", "created_at", "updated_at"}

def normalize_user_update_payload(payload: UserUpdate) -> dict[str, Any]:
    data = payload.model_dump(exclude_unset=True)
    # strip forbidden fields defensively
    for f in list(data.keys()):
        if f in FORBIDDEN_FIELDS:
            data.pop(f, None)

    # normalize email if present
    email = data.get("email")
    if email is not None:
        data["email"] = str(email).strip().lower()

    # normalize name if present
    if "name" in data and data["name"] is not None:
        data["name"] = str(data["name"]).strip()

    return data

def assert_unique_email_if_changed(db: Session, me: User, data: Mapping[str, Any]) -> None:
    if "email" not in data or data["email"] is None:
        return
    new_email = data["email"]
    if new_email == me.email:
        return
    if get_user_by_email(db, new_email) is not None:
        raise EmailExistsError


def update_me_service(db: Session, me: User, payload: UserUpdate) -> User:
    """
    Update limited, user-controlled fields for the authenticated user.
    - Forbids role/is_active/password(_hash) changes here.
    - Validates unique email on change.
    """
    data = normalize_user_update_payload(payload)
    assert_unique_email_if_changed(db, me, data)

    update_user_fields(db, me, data)

    try:
        return commit_and_refresh(db, me)
    except IntegrityError:
        db.rollback()
        # defensive fallback if a DB constraint tripped anyway
        raise EmailExistsError
