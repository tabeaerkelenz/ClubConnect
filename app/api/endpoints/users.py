from fastapi import APIRouter, Depends

from app.auth.deps import get_current_active_user
from app.core.dependencies import get_user_service
from app.models.models import User
from app.schemas.user import UserRead, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Get the current authenticated user."""
    return current_user

@router.patch("/me", response_model=UserUpdate)
def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update the current authenticated user."""
    return user_service.update_me(current_user, user_update)
