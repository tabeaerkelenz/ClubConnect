import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# load dotenv
load_dotenv()

# load from .env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Create a .env and export DATABASE_URL.")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True,              # set to False later
    pool_pre_ping=True,)    # avoids stale connections

# SessionLocal will be used to talk to DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models.py
Base = declarative_base()


