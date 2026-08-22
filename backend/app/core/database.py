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
    engine_kwargs["pool_timeout"] = 10            # Fail fast if pool is exhausted (was 30s)
    engine_kwargs["connect_args"] = {
        "connect_timeout": 10,                    # TCP connect timeout
        "application_name": "sirafit-api",        # Identify in pg_stat_activity
    }
elif DATABASE_URL.startswith("sqlite"):
    # SQLite needs a single shared connection to avoid "database is locked"
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_pool_stats():
    """Return current connection pool utilization stats.

    Used by the health endpoint to expose pool utilization % so operators can
    monitor before hitting the timeout threshold (pool_timeout=10s). Alert at
    80% utilisation. Reads from the live engine pool — never creates a new
    engine, which would produce a detached, always-empty pool and misleading 0%
    stats.
    """
    try:
        pool = engine.pool
        size = pool.size() or 1
        checked_out = pool.checkedout()
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": checked_out,
            "overflow": pool.overflow(),
            "utilization_pct": round(checked_out / size * 100, 1),
        }
    except Exception:
        # Never let pool stats crash the health endpoint.
        return {
            "pool_size": None,
            "checked_in": None,
            "checked_out": None,
            "overflow": None,
            "utilization_pct": None,
        }


Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
