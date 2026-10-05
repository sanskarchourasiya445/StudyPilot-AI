import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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

    # Calculated & Sanitized fields for frontend consumption
    display_source: Optional[str] = None
    page_count: int = 0
    chunk_count: int = 0
    file_size: Optional[int] = None
    has_summary: bool = False
    has_notes: bool = False
    has_quiz: bool = False

    @model_validator(mode="before")
    @classmethod
    def prepare_orm_data(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data

        # Handle SQLAlchemy ORM instance
        meta = {}
        if hasattr(data, "metadata_dict") and data.metadata_dict:
            meta = dict(data.metadata_dict)
        elif hasattr(data, "metadata_json") and data.metadata_json:
            try:
                raw = data.metadata_json
                meta = json.loads(raw) if isinstance(raw, str) else dict(raw)
            except Exception:
                meta = {}

        return {
            "id": getattr(data, "id", None),
            "user_id": getattr(data, "user_id", None),
            "resource_id": getattr(data, "resource_id", None),
            "source": getattr(data, "source", None),
            "source_type": getattr(data, "source_type", None),
            "title": getattr(data, "title", None),
            "workspace_id": getattr(data, "workspace_id", None),
            "status": getattr(data, "status", None),
            "metadata": meta,
            "created_at": getattr(data, "created_at", None),
            "updated_at": getattr(data, "updated_at", None),
            "has_summary": getattr(data, "has_summary", False),
            "has_notes": getattr(data, "has_notes", False),
            "has_quiz": getattr(data, "has_quiz", False),
        }

    @model_validator(mode="after")
    def sanitize_and_populate(self) -> "ResourceRead":
        meta = self.metadata or {}

        # 1. Sanitize source path: Never expose internal server filesystem paths!
        if self.source_type == "pdf":
            original_fn = meta.get("original_filename") or self.title
            if original_fn:
                self.display_source = os.path.basename(original_fn)
            else:
                self.display_source = os.path.basename(self.source)
            # Override source if it's an absolute server path
            if "\\" in self.source or "/" in self.source:
                self.source = self.display_source
        else:
            self.display_source = self.source

        # 2. Extract page_count / pages / segments
        pages_val = (
            meta.get("page_count")
            or meta.get("pages")
            or meta.get("segments")
            or meta.get("pages_or_segments")
            or 0
        )
        self.page_count = int(pages_val)

        # 3. Extract chunk_count / chunks
        chunks_val = (
            meta.get("chunk_count")
            or meta.get("chunks")
            or meta.get("chunks_created")
            or 0
        )
        self.chunk_count = int(chunks_val)

        # 4. Extract file_size
        if "file_size" in meta and meta["file_size"] is not None:
            self.file_size = int(meta["file_size"])

        return self
