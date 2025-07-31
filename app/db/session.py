from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .schema import Base

# SQLite database URL
DATABASE_URL = "sqlite:///mlb_stats.db"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a configured "SessionLocal" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize the database
Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency injection for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()