from typing import Optional
from sqlalchemy.orm import Session
from backend.app.core.security import get_password_hash, verify_password
from backend.app.db.models.user import User
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.auth import UserRegister


class DuplicateUserError(Exception):
    """Raised when registering a user with an existing email address."""


class AuthService:
    def __init__(self, user_repo: UserRepository = UserRepository()) -> None:
        self._user_repo = user_repo

    def register_user(self, db: Session, user_in: UserRegister) -> User:
        existing_user = self._user_repo.get_by_email(db, user_in.email)
        if existing_user:
            raise DuplicateUserError(f"A user with email '{user_in.email}' already exists.")

        pwd_hash = get_password_hash(user_in.password)
        return self._user_repo.create(
            db=db,
            email=user_in.email,
            password_hash=pwd_hash,
            name=user_in.name,
        )

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        user = self._user_repo.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
