from typing import Union, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.auth.jwt_utils import decode_token
from app.db.deps import get_db
from app.models.models import UserRole, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
RoleArg = Union[UserRole, str]


def _cred_exception():
    """
    Helper to return a 401 HTTPException for invalid credentials
    :return: 401 Unauthorized HTTPException
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to get the current user based on the JWT token
    :param db: SQLAlchemy Session, provided by Depends
    :param token: Dependency injection of the OAuth2 token (JWT)
    :return: user instance
    :raises HTTPException 401: if the token is invalid or user not found/inactive
    """
    try:
        payload = decode_token(token)
        sub = (
            payload.get("sub")
            if isinstance(payload, dict)
            else getattr(payload, "sub", None)
        )  # make the sub accept dict as well
        if not sub:
            raise _cred_exception()
        user_id = int(sub)
    except (JWTError, ValueError, TypeError):
        raise _cred_exception()

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise _cred_exception()
    return user


def get_current_active_user(user: User = Depends(get_current_user)):
    """
    Dependency to get the current active user
    :param user: dependency injection of the current user
    :return: user instance
    """
    if not user.is_active:
        raise _cred_exception()
    return user


def require_roles(*roles: RoleArg) -> Callable:
    """
    Dependency factory to require specific user roles for a route
    :param roles: Roles to allow (UserRole enum or str)
    :return: user instance if role is allowed
    """
    allowed = {r.value if isinstance(r, UserRole) else r for r in roles}
    if not allowed:
        raise ValueError("Invalid roles")

    def _dep(user=Depends(get_current_user)):
        user_role = getattr(user.role, "value", str(user.role)).lower()
        if user_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden, role '{user_role}' not allowed",
            )
        return user

    return _dep
