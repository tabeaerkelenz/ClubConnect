import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# load dotenv
# -> .../ClubConnect (inner)
PROJECT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_DIR / ".env"
load_dotenv(ENV_PATH)

# load from .env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        f"DATABASE_URL is not set. Create a .env and export DATABASE_URL. Tried: {ENV_PATH}"
    )

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True,  # set to False later
    pool_pre_ping=True,  # avoids stale connections
    future=True,  # 2.0 style
)

# set UTC time stamps in Postgres


@event.listens_for(engine, "connect")
def set_utc(dbapi_connection, _):
    module = getattr(dbapi_connection, "__class__", type(dbapi_connection)).__module__
    if not (module.startswith("psycopg2") or module.startswith("psycopg")):
        return
    with dbapi_connection.cursor() as cur:
        cur.execute("SET TIME ZONE 'UTC'")


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
