from .settings import settings
from .database import engine, Base, get_db

# Create all database tables
Base.metadata.create_all(bind=engine)
