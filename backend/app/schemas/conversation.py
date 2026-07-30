import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from backend.app.schemas.chat import SourceCitation


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(None, description="Conversation title")
    resource_id: Optional[str] = Field(None, description="Optional resource_id scope")


class MessageRead(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: List[SourceCitation] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("sources", mode="before")
    @classmethod
    def parse_sources_json(cls, v: Any, info: Any) -> List[Dict[str, Any]]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return []


class ConversationRead(BaseModel):
    id: str
    user_id: str
    resource_id: Optional[str] = None
    title: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
