from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ClubConnect.app.auth.deps import get_current_active_user
from ClubConnect.app.db.database import get_db
from ClubConnect.app.crud.user import authenticate_user
from ClubConnect.app.auth.schemas import Token
from ClubConnect.app.auth.jwt import create_access_token
from ClubConnect.app.db.models import User
from ClubConnect.app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    sub = user.email or user.name
    return {"access_token": create_access_token(sub=sub), "token_type": "bearer"}

@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user
