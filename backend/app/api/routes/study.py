from typing import List, Optional
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


@router.post(
    "/{resource_id}/summary",
    response_model=SummaryResponse,
    summary="Generate or fetch summary for a resource",
    description="Returns backend-cached or newly map-reduced summary for a resource.",
)
@router.get(
    "/{resource_id}/summary",
    response_model=SummaryResponse,
    summary="Get summary for a resource",
)
def get_summary(
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
