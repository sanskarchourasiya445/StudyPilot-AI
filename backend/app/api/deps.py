from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ai_engine.engine import AIEngine
from backend.app.ai.engine_provider import get_ai_engine
from backend.app.core.config import settings
from backend.app.core.security import decode_access_token
from backend.app.db.models.user import User
from backend.app.db.session import SessionLocal
from backend.app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


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


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Dependency that decodes the JWT access token and returns the current authenticated user.

    Raises HTTP 401 Unauthorized if the token is invalid, expired, or the user does not exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise credentials_exception

    return user
