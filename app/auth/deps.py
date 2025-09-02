from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from ClubConnect.app.db.database import get_db
from ClubConnect.app.auth.jwt import decode_token
from ClubConnect.app.crud.user import get_user_by_email, get_user_by_username

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def _cred_exception():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        sub = payload.sub
        if not sub:
            raise _cred_exception()
    except JWTError:
        raise _cred_exception()

    user = get_user_by_email(db, sub) or get_user_by_username(db, sub)
    if not user or not user.is_active:
        raise _cred_exception()
    return user

def get_current_active_user(user = Depends(get_current_user)):
    if not user.is_active:
        raise _cred_exception()
    return user