import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query string")
    top_k: int = Field(4, ge=1, le=20, description="Number of chunks to retrieve")


class SearchResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved SearchResult list")


class SummaryRequest(BaseModel):
    force_regenerate: bool = Field(False, description="Bypass cache and force fresh summarization")


class SummaryResponse(BaseModel):
    id: str
    resource_id: str
    summary: str
    version: str = "1.0"
    config_hash: str
    cached: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotesRequest(BaseModel):
    style: str = Field("bullet", description="Note style: 'bullet' or 'cornell'")
    force_regenerate: bool = Field(False, description="Bypass summary cache and force re-summarization")


class NotesResponse(BaseModel):
    id: str
    resource_id: str
    style: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuizRequest(BaseModel):
    question_count: int = Field(5, ge=1, le=20, description="Number of questions to generate")
    difficulty: str = Field("medium", description="Difficulty: 'easy', 'medium', or 'hard'")
    force_regenerate: bool = Field(False, description="Bypass summary cache and force re-summarization")


class QuizQuestionSchema(BaseModel):
    question: str
    options: List[str]
    correct_answer_index: int
    explanation: str


class QuizResponse(BaseModel):
    id: str
    resource_id: str
    difficulty: str
    question_count: int
    questions: List[QuizQuestionSchema] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
