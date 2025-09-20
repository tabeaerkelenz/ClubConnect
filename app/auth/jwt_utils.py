from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError
from app.auth.schemas import TokenPayload
from app.core.config import settings

class AuthError(Exception):
    """Domain error for auth problems."""
    pass

def _secret(val):  # handles SecretStr or plain str
    return val.get_secret_value() if hasattr(val, "get_secret_value") else val


def create_access_token(*, sub: str, expire_minutes: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    exp_min = expire_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    exp = now + timedelta(minutes=exp_min)
    payload = {
        "sub": sub.strip().lower(),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }

    key = _secret(settings.SECRET_KEY)
    encoded_jwt = jwt.encode(payload, key, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> TokenPayload:
    key = _secret(settings.SECRET_KEY)
    try:
        data = jwt.decode(
            token, key,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False},
        )
        if "sub" not in data or "exp" not in data:
            raise JWTError("missing required claim")
        return TokenPayload(**data)
    except ExpiredSignatureError as e:
        raise AuthError("token_expired") from e
    except JWTError as e:
        raise AuthError("invalid_token") from e

