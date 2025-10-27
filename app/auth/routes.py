from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.deps import get_current_active_user
from app.core.security import hash_password
from app.crud.user import authenticate_user
from app.auth.schemas import Token
from app.auth.jwt_utils import create_access_token
from app.db.deps import get_db
from app.db.models import User, UserRole
from app.schemas.user import UserRead, UserUpdate, PasswordChange, UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Self-signup: create a new user and return a JWT access token.
    - Normalizes email
    - Hashes password (never store plaintext)
    - 409 if email already used
    """
    if not payload.email or not payload.password:
        raise HTTPException(status_code=422, detail="email and password are required")

    email = payload.email.strip().lower()
    user = User(
        name=payload.name,
        email=email,
        password_hash=hash_password(payload.password),  # NOTE: store hash, not plaintext
        is_active=True,
        role=UserRole.athlete
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if getattr(getattr(e, "orig", None), "pgcode", None) == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Could not create user")
    db.refresh(user)
    # Use user.id as JWT subject; it’s stable even if email changes
    token = create_access_token(sub=str(user.id))
    return {"access_token": token, "token_type": "bearer"}


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

    return {"access_token": create_access_token(sub=str(user.id)), "token_type": "bearer"}


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
