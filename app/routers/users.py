from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ClubConnect.app.db.database import get_db
from ClubConnect.app.schemas.user import UserRead, UserCreate
from ClubConnect.app.services.user import create_user_service

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(payload: UserCreate, db: Session = Depends(get_db)):
    return create_user_service(db, name=payload.name, email=payload.email, password=payload.password)