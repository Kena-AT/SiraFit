from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# DATABASE_URL is a plain str — works with both PostgreSQL and SQLite (for tests)
DATABASE_URL = settings.DATABASE_URL

engine_kwargs = {"echo": False}
if DATABASE_URL.startswith("postgres"):
    # Production pool tuning — handles concurrent users without queuing requests.
    # Ponytail: defaults (pool_size=5) queue under any real load.
    engine_kwargs["pool_size"] = 20               # Steady-state connections
    engine_kwargs["max_overflow"] = 10            # Burst capacity beyond pool_size
    engine_kwargs["pool_pre_ping"] = True         # Detect stale connections
    engine_kwargs["pool_recycle"] = 300           # 5 min — recycle before Neon idle-kills
    engine_kwargs["pool_timeout"] = 30            # Fail fast if pool is exhausted
    engine_kwargs["connect_args"] = {
        "connect_timeout": 10,                    # TCP connect timeout
        "application_name": "sirafit-api",        # Identify in pg_stat_activity
    }
elif DATABASE_URL.startswith("sqlite"):
    # SQLite needs a single shared connection to avoid "database is locked"
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
