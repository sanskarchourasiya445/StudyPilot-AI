from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    source: str = Field(..., description="Source document or URL")
    content: str = Field(..., description="Retrieved chunk content")
    score: float = Field(0.0, description="Relevance / similarity score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")


class ChatScope(BaseModel):
    mode: str = Field("all", description="Scope mode: 'all' or 'selected'")
    resource_ids: List[str] = Field(default_factory=list, description="List of selected resource_ids when mode='selected'")


class ChatRequest(BaseModel):
    message: str = Field(..., description="User question or prompt")
    resource_id: Optional[str] = Field(None, description="Legacy single resource_id for backward compatibility")
    resource_ids: Optional[List[str]] = Field(None, description="Multi-resource selection IDs")
    scope: Optional[ChatScope] = Field(None, description="Explicit chat resource scope")
    conversation_id: Optional[str] = Field(None, description="Optional conversation_id for history tracking")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Grounded response from AI Engine")
    sources: List[SourceCitation] = Field(default_factory=list, description="Source citations")
    scope: ChatScope = Field(default_factory=ChatScope, description="Explicit resource scope used for retrieval")
    resource_id: Optional[str] = Field(None, description="Legacy single resource_id for compatibility")
    resource_ids: List[str] = Field(default_factory=list, description="Selected resource_ids")
    conversation_id: Optional[str] = Field(None, description="Conversation scope")
