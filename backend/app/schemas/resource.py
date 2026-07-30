import json
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class YouTubeIngestRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL (e.g. https://www.youtube.com/watch?v=...)")
    title: Optional[str] = Field(None, description="Optional custom title")


class ResourceRead(BaseModel):
    id: str
    user_id: str
    resource_id: str
    source: str
    source_type: str
    title: Optional[str] = None
    workspace_id: Optional[str] = None
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("metadata", mode="before")
    @classmethod
    def parse_metadata_json(cls, v: Any, info: Any) -> Dict[str, Any]:
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return {}
