import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "pdf", "txt", "youtube"
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    workspace_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ready", nullable=False)  # "processing", "ready", "failed"
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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

    user = relationship("User", back_populates="resources")

    @property
    def metadata_dict(self) -> Dict[str, Any]:
        if not self.metadata_json:
            return {}
        try:
            return json.loads(self.metadata_json)
        except Exception:
            return {}

    @metadata_dict.setter
    def metadata_dict(self, val: Dict[str, Any]) -> None:
        self.metadata_json = json.dumps(val) if val else None
