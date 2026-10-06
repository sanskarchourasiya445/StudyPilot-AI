from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.app.core.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 300,  # Recycle connections every 5 min for serverless PostgreSQL (Neon)
}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # Production connection pool sized for single container / serverless Neon
    engine_kwargs.update({"pool_size": 5, "max_overflow": 10})

engine = create_engine(
    db_url,
    connect_args=connect_args,
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
