import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class MasteryRecord(Base):
    __tablename__ = "mastery_records"
    __table_args__ = (
        UniqueConstraint("user_id", "topic", name="uq_user_topic_mastery"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    mastery_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    next_review_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    @property
    def status(self) -> str:
        score = self.mastery_score
        if score < 40:
            return "Needs Attention"
        elif score < 70:
            return "Needs Practice"
        elif score < 85:
            return "Good"
        else:
            return "Mastered"

    @property
    def recommendation(self) -> str:
        score = self.mastery_score
        if score < 40:
            return f"You are currently weak in '{self.topic}'. Review your study materials and attempt another practice quiz."
        elif score < 70:
            return f"You are developing understanding in '{self.topic}'. Additional practice quizzes recommended."
        elif score < 85:
            return f"Good mastery of '{self.topic}'! Review remaining key concepts to achieve complete mastery."
        else:
            return f"Strong mastery achieved for '{self.topic}'! Excellent progress."
