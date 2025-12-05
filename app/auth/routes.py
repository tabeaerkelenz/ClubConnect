from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.deps import get_current_active_user
from app.core.dependencies import get_user_service
from app.exceptions.base import EmailExistsError, IncorrectPasswordError
from app.auth.schemas import Token
from app.auth.jwt_utils import create_access_token
from app.models.models import User
from app.schemas.user import PasswordChange, UserCreate
from app.services.user import UserService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_user(user_create: UserCreate, user_service: UserService = Depends(get_user_service)):
    """
    Self-signup: create a new user and return a JWT access token.
    - 422 if email or password missing
    - call create_user from UserService
    - 409 if email already used
    - return JWT token
    - Password is hashed in UserService.create_user
    """
    if not user_create.email or not user_create.password:
        raise HTTPException(status_code=422, detail="email and password are required")

    try:
        user = user_service.create_user(user_create)
    except EmailExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
    )

    token = create_access_token(sub=user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service),
):
    """Authenticate user and return a JWT token"""
    email = form_data.username
    user = user_service.authenticate(email=email, password=form_data.password)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": create_access_token(sub=user.id), "token_type": "bearer"}


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """Change password for the current authenticated user"""
    try:
        user_service.change_password(
            user=current_user,
            old_password=payload.old_password,
            new_password=payload.new_password,
        )
    except IncorrectPasswordError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password",
        )

    return None