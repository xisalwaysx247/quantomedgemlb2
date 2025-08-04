from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .schema import Base
import os
import shutil
from datetime import datetime

# SQLite database URL - using absolute path for better persistence
DATABASE_FILE = "mlb_stats.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Create the SQLAlchemy engine with persistence optimizations
engine = create_engine(
    DATABASE_URL, 
    connect_args={
        "check_same_thread": False,
        "timeout": 30  # 30 second timeout for better reliability
    },
    pool_pre_ping=True,  # Verify connections before use
    echo=False  # Set to True for SQL debugging
)

# Create a configured "SessionLocal" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize the database and ensure Pick table exists
def initialize_database():
    """Initialize database and ensure all tables exist"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

def backup_database():
    """Create a backup of the database"""
    if os.path.exists(DATABASE_FILE):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"mlb_stats_backup_{timestamp}.db"
        try:
            shutil.copy2(DATABASE_FILE, backup_file)
            print(f"✅ Database backed up to {backup_file}")
            return backup_file
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    return None

def verify_picks_table():
    """Verify the picks table exists and is accessible"""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'picks' in tables:
            print("✅ Pick Tank table verified")
            return True
        else:
            print("❌ Pick Tank table missing - recreating...")
            Base.metadata.create_all(bind=engine)
            return True
    except Exception as e:
        print(f"❌ Pick Tank verification failed: {e}")
        return False

# Initialize on import
initialize_database()
verify_picks_table()

def get_db():
    """Dependency injection for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()