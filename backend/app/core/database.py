from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# DATABASE_URL is a plain str — works with both PostgreSQL and SQLite (for tests)
DATABASE_URL = settings.DATABASE_URL

engine_kwargs = {"echo": False}
if DATABASE_URL.startswith("postgres"):
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 3600

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
