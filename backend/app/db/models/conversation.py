import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey("resources.resource_id", ondelete="SET NULL"), nullable=True, index=True
    )
    scope_mode: Mapped[str] = mapped_column(
        String(50), default="all", nullable=False
    )
    resource_ids_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), default="New Conversation", nullable=False)

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

    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )

    @property
    def resource_ids(self) -> List[str]:
        if self.resource_ids_json:
            try:
                res = json.loads(self.resource_ids_json)
                if isinstance(res, list):
                    return res
            except Exception:
                pass
        if self.resource_id:
            return [self.resource_id]
        return []

    @resource_ids.setter
    def resource_ids(self, val: Optional[List[str]]) -> None:
        if val is None:
            self.resource_ids_json = None
        else:
            self.resource_ids_json = json.dumps(val)
