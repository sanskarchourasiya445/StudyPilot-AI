import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid, index=True
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # "user", "assistant", "system"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    conversation = relationship("Conversation", back_populates="messages")

    @property
    def sources_list(self) -> List[Dict[str, Any]]:
        if not self.sources_json:
            return []
        try:
            return json.loads(self.sources_json)
        except Exception:
            return []

    @sources_list.setter
    def sources_list(self, val: List[Dict[str, Any]]) -> None:
        self.sources_json = json.dumps(val) if val else None
