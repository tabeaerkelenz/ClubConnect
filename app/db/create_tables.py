from database import Base, engine


def create_tables():
    """Create all tables in the database."""
    print("Creating tables (if not exist)...")
    Base.metadata.create_all(bind=engine)
    print("<UNK> Tables created.")


# if __name__ == "__main__":
    # create_tables()
