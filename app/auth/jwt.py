from datetime import datetime, timedelta, timezone
from jose import jwt

from ClubConnect.app.auth.schemas import TokenPayload
from ClubConnect.app.core.config import settings

def create_access_token(*, sub: str, expire_minutes: int | None = None) -> str: # spelling mistake from crate_access_token to create_access_token
    exp_min = expire_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    exp = datetime.now(timezone.utc) + timedelta(minutes=exp_min)
    payload = {
        "sub": sub,
        "exp": exp,
    }
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> TokenPayload:
    data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    return TokenPayload(**data)

# rebase git 