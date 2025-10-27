# app/db/deps.py
from typing import Iterator
from sqlalchemy.orm import Session
from app.db.database import build_session_maker

# Default sessionmaker uses DATABASE_URL from env/.env (Postgres in dev/prod)
SessionLocal = build_session_maker()

def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
