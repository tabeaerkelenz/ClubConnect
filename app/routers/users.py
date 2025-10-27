# app/routers/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import get_current_active_user
from app.db.deps import get_db
from app.db.models import User
from app.schemas.user import UserRead, UserUpdate
from app.services.user import update_me_service

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Get the current authenticated user."""
    return current_user

@router.patch("/me", response_model=UserRead)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update the current authenticated user."""
    return update_me_service(db, current_user, payload)
