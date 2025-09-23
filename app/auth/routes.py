from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.deps import get_current_active_user
from app.db.database import get_db
from app.crud.user import authenticate_user
from app.auth.schemas import Token
from app.auth.jwt_utils import create_access_token
from app.db.models import User
from app.schemas.user import UserRead, UserUpdate, PasswordChange

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Authenticate user and return a JWT token"""
    email = form_data.username.strip().lower()
    user = authenticate_user(db, email=email, password=form_data.password)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": create_access_token(sub=email), "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Get the current authenticated user"""
    return current_user


# add here the other me endpoints you already have in Notion!


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update the current authenticated user"""
    data = payload.model_dump(exclude_unset=True)

    data.pop("is_active", None)

    if "email" in data and data["email"] is not None:
        data["email"] = str(data["email"]).strip().lower()

    for k, v in data.items():
        setattr(current_user, k, v)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    db.refresh(current_user)
    return current_user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Change password for the current authenticated user"""
    if not current_user.check_password(payload.old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password"
        )

    current_user.password = payload.new_password
    db.add(current_user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    return None
