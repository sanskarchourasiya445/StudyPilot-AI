from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.db.models.user import User
from backend.app.schemas.mastery import (
    DifficultyRecommendationResponse,
    KnowledgeGapResponse,
    MasteryRecordResponse,
    QuizAttemptResponse,
    QuizSubmitRequest,
)
from backend.app.services.study_service import StudyService, ResourceNotFoundError

router = APIRouter(prefix="/mastery", tags=["Mastery & Knowledge Gaps"])
study_service = StudyService()


@router.get(
    "",
    response_model=List[MasteryRecordResponse],
    summary="Get all topic mastery records for current user",
)
def get_mastery(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MasteryRecordResponse]:
    return study_service.get_user_mastery(db, current_user)


@router.get(
    "/gaps",
    response_model=KnowledgeGapResponse,
    summary="Get knowledge gaps (topics with mastery < 70)",
)
def get_knowledge_gaps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeGapResponse:
    return study_service.get_user_knowledge_gaps(db, current_user)


@router.get(
    "/difficulty",
    response_model=DifficultyRecommendationResponse,
    summary="Get recommended quiz difficulty based on topic mastery",
)
def get_topic_difficulty_query(
    topic: str = Query(..., description="Topic name to check mastery for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DifficultyRecommendationResponse:
    return study_service.get_recommended_difficulty_for_topic(db, current_user, topic)


@router.get(
    "/{topic}/difficulty",
    response_model=DifficultyRecommendationResponse,
    summary="Get recommended quiz difficulty for a specific topic path",
)
def get_topic_difficulty_path(
    topic: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DifficultyRecommendationResponse:
    return study_service.get_recommended_difficulty_for_topic(db, current_user, topic)


@router.post(
    "/quizzes/{quiz_id}/submit",
    response_model=QuizAttemptResponse,
    summary="Submit quiz attempt and update topic mastery",
)
def submit_quiz_result(
    quiz_id: str,
    payload: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizAttemptResponse:
    try:
        return study_service.submit_quiz_attempt(
            db,
            current_user,
            quiz_id,
            score=payload.score,
            total_questions=payload.total_questions,
            topic_override=payload.topic,
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
