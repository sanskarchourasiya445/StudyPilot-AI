from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    source: str = Field(..., description="Source document or URL")
    content: str = Field(..., description="Retrieved chunk content")
    score: float = Field(0.0, description="Relevance / similarity score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")


class ChatRequest(BaseModel):
    message: str = Field(..., description="User question or prompt")
    resource_id: Optional[str] = Field(None, description="Optional resource_id to restrict RAG context")
    conversation_id: Optional[str] = Field(None, description="Optional conversation_id for history tracking")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Grounded response from AI Engine")
    sources: List[SourceCitation] = Field(default_factory=list, description="Source citations")
    resource_id: Optional[str] = Field(None, description="Resource scope used")
    conversation_id: Optional[str] = Field(None, description="Conversation scope")
