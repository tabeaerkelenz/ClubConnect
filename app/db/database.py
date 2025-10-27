from typing import Iterator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

def build_engine(url: str | None = None):
    # Only import settings if we actually need the default
    if url is None:
        from app.core.config import settings  # lazy import!
        url = settings.DATABASE_URL

    if url.startswith("sqlite"):
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool if url.endswith(":memory:") else None,
        )
        @event.listens_for(engine, "connect")
        def _fk_on(dbapi_conn, _):
            try:
                dbapi_conn.execute("PRAGMA foreign_keys=ON;")
            except Exception:
                pass
        return engine

    return create_engine(url, pool_pre_ping=True)


def build_session_maker(url: Optional[str] = None):
    engine = build_engine(url)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

