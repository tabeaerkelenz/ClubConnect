from app.db.base import Base
from database import build_engine


def create_tables():
    """Create all tables in the database."""
    print("Creating tables (if not exist)...")
    Base.metadata.create_all(bind=build_engine)
    print("<UNK> Tables created.")


# if __name__ == "__main__":
    # create_tables()
