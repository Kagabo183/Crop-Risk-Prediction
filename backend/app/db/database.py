from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Configure connection pool for multi-worker deployment
# With multiple Celery workers, keep pool size small per process
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=2,          # Max persistent connections per worker process
    max_overflow=3,       # Additional connections when pool exhausted
    pool_pre_ping=True,   # Verify connections before using
    pool_recycle=3600,    # Recycle connections after 1 hour
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
