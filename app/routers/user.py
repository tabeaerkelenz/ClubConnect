from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ClubConnect.app.auth.deps import require_roles
from ClubConnect.app.db.database import get_db
from ClubConnect.app.db.models import UserRole
from ClubConnect.app.schemas.user import UserCreate, UserUpdate, UserRead
from ClubConnect.app.crud.user import create_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        user = create_user(db, name=payload.name, email=payload.email, password=payload.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return user

