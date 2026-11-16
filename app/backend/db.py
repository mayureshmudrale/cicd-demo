from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from models import Base

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    # Recycle connections before the DB side (or an intermediate proxy/LB)
    # drops them for being idle too long - avoids stale-connection errors
    # under low traffic without needing a dedicated health-check loop.
    pool_recycle=1800,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create any tables declared on Base that don't exist yet."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
