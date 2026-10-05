from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class QuizSubmitRequest(BaseModel):
    score: int = Field(..., ge=0, description="Number of correct answers")
    total_questions: int = Field(..., gt=0, description="Total number of questions")
    topic: Optional[str] = Field(None, description="Optional topic override")


class QuizAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    quiz_id: str
    resource_id: Optional[str]
    topic: str
    score: int
    total_questions: int
    percentage: float
    attempted_at: datetime
    mastery_score: int
    mastery_status: str
    recommendation: str
    next_review_at: Optional[datetime] = None
    review_interval_days: int = 1


class MasteryRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    topic: str
    mastery_score: int
    status: str
    total_questions: int
    correct_answers: int
    total_attempts: int
    last_attempt_at: datetime
    recommendation: str


class KnowledgeGapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_topics: int
    gaps_count: int
    mastered_count: int
    gaps: List[MasteryRecordResponse]
    all_mastery: List[MasteryRecordResponse]


class DifficultyRecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    topic: str
    mastery_score: Optional[int]
    recommended_difficulty: str
    reason: str
