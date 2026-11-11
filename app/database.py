from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# "engine" = the connection to the database file
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # needed only for SQLite
)

# SessionLocal = a "conversation" with the database, one per request
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base = the parent class all your tables will inherit from
Base = declarative_base()

def get_db():
    """FastAPI uses this to give each request its own database session,
    and close it afterwards. Copy-paste, don't modify."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
