from typing import Optional
from sqlalchemy.orm import Session
from backend.app.db.models.user import User


class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower()).first()

    @staticmethod
    def create(
        db: Session,
        email: str,
        password_hash: str,
        name: Optional[str] = None,
    ) -> User:
        user = User(
            email=email.lower().strip(),
            password_hash=password_hash,
            name=name.strip() if name else None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
