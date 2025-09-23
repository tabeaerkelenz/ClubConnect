from pydantic import BaseModel


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for JWT token payload"""
    sub: str  # Subject (identifier)
    exp: int | None = None  # Expiration (timestamp for token invalidity)
