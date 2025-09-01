import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# load dotenv
PROJECT_DIR = Path(__file__).resolve().parents[2]   # -> .../ClubConnect (inner)
ENV_PATH = PROJECT_DIR / ".env"
load_dotenv(ENV_PATH)

# load from .env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Create a .env and export DATABASE_URL. Tried: {ENV_PATH}")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True,              # set to False later
    pool_pre_ping=True,)    # avoids stale connections

# SessionLocal will be used to talk to DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models.py
Base = declarative_base()

# DB session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
