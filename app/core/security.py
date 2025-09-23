from passlib.context import CryptContext

# setup how passwords are hashed/verified
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)  # returns secure bcrypt hash


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # checks if plain matches the stored hash
    return pwd_ctx.verify(plain_password, hashed_password)
