from database import Base, engine
from models import Clubs

print("📦 Creating tables...")
Base.metadata.create_all(bind=engine)
