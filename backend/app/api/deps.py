from typing import Generator
from sqlalchemy.orm import Session
from ai_engine.engine import AIEngine
from backend.app.ai.engine_provider import get_ai_engine
from backend.app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine() -> AIEngine:
    """Dependency that provides the singleton AIEngine instance."""
    return get_ai_engine()
