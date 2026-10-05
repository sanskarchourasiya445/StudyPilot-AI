from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ai_engine.engine import AIEngine, EngineError
from backend.app.api.deps import get_current_user, get_db, get_engine
from backend.app.db.models.user import User
from backend.app.schemas.study import (
    NotesRequest,
    NotesResponse,
    QuizRequest,
    QuizResponse,
    SearchRequest,
    SearchResponse,
    SummaryRequest,
    SummaryResponse,
)
from backend.app.services.resource_service import ResourceNotFoundError
from backend.app.services.study_service import StudyService

router = APIRouter(prefix="/resources", tags=["Study Capabilities"])
study_service = StudyService()


@router.post(
    "/{resource_id}/search",
    response_model=SearchResponse,
    summary="Search resource chunks (Retrieval only)",
    description="Perform vector search across chunks belonging to a specific resource without an LLM call.",
)
def search_resource(
    resource_id: str,
    request: SearchRequest,
    db: Session = Depends(get_db),
    engine: AIEngine = Depends(get_engine),
    current_user: User = Depends(get_current_user),
) -> SearchResponse:
    try:
        return study_service.search(
            db, engine, current_user, resource_id, request.query, top_k=request.top_k
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{resource_id}/summary",
    response_model=SummaryResponse,
    summary="Get cached summary for a resource",
)
def get_existing_summary(
    resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SummaryResponse:
    try:
        summary = study_service.get_existing_summary(db, current_user, resource_id)
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No cached summary found for this resource.",
            )
        return summary
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{resource_id}/summary",
    response_model=SummaryResponse,
    summary="Generate or regenerate summary for a resource",
)
def generate_summary(
    resource_id: str,
    request: Optional[SummaryRequest] = None,
    db: Session = Depends(get_db),
    engine: AIEngine = Depends(get_engine),
    current_user: User = Depends(get_current_user),
) -> SummaryResponse:
    force_regen = request.force_regenerate if request else False
    try:
        return study_service.get_summary(
            db, engine, current_user, resource_id, force_regenerate=force_regen
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {exc}",
        ) from exc


@router.post(
    "/{resource_id}/notes",
    response_model=NotesResponse,
    summary="Generate structured study notes",
    description="Generates bullet-point or Cornell-style study notes for a resource.",
)
def generate_notes(
    resource_id: str,
    request: NotesRequest,
    db: Session = Depends(get_db),
    engine: AIEngine = Depends(get_engine),
    current_user: User = Depends(get_current_user),
) -> NotesResponse:
    try:
        return study_service.generate_notes(
            db,
            engine,
            current_user,
            resource_id,
            style=request.style,
            force_regenerate=request.force_regenerate,
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Notes generation failed: {exc}",
        ) from exc


@router.get(
    "/{resource_id}/notes",
    response_model=NotesResponse,
    summary="Fetch existing study notes",
)
def get_notes(
    resource_id: str,
    style: str = Query("bullet", description="Note style: 'bullet' or 'cornell'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotesResponse:
    try:
        notes = study_service.get_existing_notes(db, current_user, resource_id, style=style)
        if not notes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No '{style}' notes found for resource. Generate them using POST first.",
            )
        return notes
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{resource_id}/quiz",
    response_model=QuizResponse,
    summary="Generate a multiple-choice quiz",
    description="Generates multiple-choice quiz questions for a resource.",
)
def generate_quiz(
    resource_id: str,
    request: QuizRequest,
    db: Session = Depends(get_db),
    engine: AIEngine = Depends(get_engine),
    current_user: User = Depends(get_current_user),
) -> QuizResponse:
    try:
        return study_service.generate_quiz(
            db,
            engine,
            current_user,
            resource_id,
            question_count=request.question_count,
            difficulty=request.difficulty,
            force_regenerate=request.force_regenerate,
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz generation failed: {exc}",
        ) from exc


@router.get(
    "/{resource_id}/quizzes",
    response_model=List[QuizResponse],
    summary="List generated quizzes for a resource",
)
def list_quizzes(
    resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[QuizResponse]:
    try:
        return study_service.list_quizzes(db, current_user, resource_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/quizzes/{quiz_id}/submit",
    summary="Submit quiz attempt and update mastery",
    description="Submits a completed quiz score, records attempt history, and updates topic mastery.",
)
def submit_quiz_attempt(
    quiz_id: str,
    request: Any = Depends(lambda: None),
    score: int = Query(..., ge=0),
    total_questions: int = Query(..., gt=0),
    topic_override: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return study_service.submit_quiz_attempt(
            db, current_user, quiz_id, score=score, total_questions=total_questions, topic_override=topic_override
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{resource_id}/summary",
    summary="Delete summary for a resource",
)
def delete_summary(
    resource_id: str,
    db: Session = Depends(get_db),
    engine: AIEngine = Depends(get_engine),
    current_user: User = Depends(get_current_user),
):
    try:
        deleted = study_service.delete_summary(db, engine, current_user, resource_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No summary found to delete.")
        return {"message": "Summary deleted successfully."}
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{resource_id}/notes",
    summary="Delete study notes for a resource",
)
def delete_notes(
    resource_id: str,
    style: Optional[str] = Query(None, description="Optional style filter: 'bullet' or 'cornell'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        deleted = study_service.delete_notes(db, current_user, resource_id, style=style)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No notes found to delete.")
        return {"message": "Study notes deleted successfully."}
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{resource_id}/quizzes",
    summary="Delete quizzes for a resource",
)
def delete_quizzes(
    resource_id: str,
    quiz_id: Optional[str] = Query(None, description="Optional specific quiz_id to delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        deleted = study_service.delete_quizzes(db, current_user, resource_id, quiz_id=quiz_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No quizzes found to delete.")
        return {"message": "Quizzes deleted successfully."}
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
