import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from ai_engine.config import get_summary_config_hash
from ai_engine.engine import AIEngine
from backend.app.db.models.user import User
from backend.app.repositories.resource_repository import ResourceRepository
from backend.app.repositories.study_repository import StudyRepository
from backend.app.schemas.study import (
    NotesResponse,
    QuizQuestionSchema,
    QuizResponse,
    SearchResponse,
    SummaryResponse,
)
from backend.app.services.resource_service import ResourceNotFoundError


class StudyService:
    def __init__(
        self,
        resource_repo: ResourceRepository = ResourceRepository(),
        study_repo: StudyRepository = StudyRepository(),
    ) -> None:
        self._resource_repo = resource_repo
        self._study_repo = study_repo

    def search(
        self,
        db: Session,
        engine: AIEngine,
        user: User,
        resource_identifier: str,
        query: str,
        top_k: int = 4,
    ) -> SearchResponse:
        resource = self._resource_repo.get_by_user(db, user.id, resource_identifier)
        if not resource:
            raise ResourceNotFoundError(
                f"Resource '{resource_identifier}' not found or not owned by user."
            )

        raw_results = engine.search(query, top_k=top_k, resource_id=resource.resource_id)

        results_list: List[Dict[str, Any]] = []
        for r in raw_results:
            if hasattr(r, "page_content"):
                content_str = r.page_content
                meta_dict = getattr(r, "metadata", {}) or {}
                source_str = meta_dict.get("source", "")
                score_val = meta_dict.get("score", 0.0)
            elif isinstance(r, dict):
                content_str = r.get("content", "")
                meta_dict = r.get("metadata", {}) or {}
                source_str = r.get("source", "") or meta_dict.get("source", "")
                score_val = float(r.get("score", 0.0))
            else:
                content_str = getattr(r, "content", str(r))
                meta_dict = getattr(r, "metadata", {}) or {}
                source_str = getattr(r, "source", "")
                score_val = getattr(r, "score", 0.0)

            results_list.append(
                {
                    "content": content_str,
                    "score": score_val,
                    "source": source_str,
                    "metadata": meta_dict,
                }
            )

        return SearchResponse(results=results_list)

    def get_summary(
        self,
        db: Session,
        engine: AIEngine,
        user: User,
        resource_identifier: str,
        force_regenerate: bool = False,
    ) -> SummaryResponse:
        resource = self._resource_repo.get_by_user(db, user.id, resource_identifier)
        if not resource:
            raise ResourceNotFoundError(
                f"Resource '{resource_identifier}' not found or not owned by user."
            )

        cfg_hash = get_summary_config_hash()

        if not force_regenerate:
            db_summary = self._study_repo.get_summary(db, resource.resource_id)
            if db_summary and db_summary.config_hash == cfg_hash:
                return SummaryResponse(
                    id=db_summary.id,
                    resource_id=resource.resource_id,
                    summary=db_summary.summary,
                    version=db_summary.version,
                    config_hash=db_summary.config_hash,
                    cached=True,
                    created_at=db_summary.created_at,
                )

        summary_text = engine.summarize(
            resource.source, resource_id=resource.resource_id, force_regenerate=force_regenerate
        )

        saved = self._study_repo.save_summary(
            db, resource.resource_id, summary_text, cfg_hash
        )

        return SummaryResponse(
            id=saved.id,
            resource_id=resource.resource_id,
            summary=saved.summary,
            version=saved.version,
            config_hash=saved.config_hash,
            cached=False,
            created_at=saved.created_at,
        )

    def generate_notes(
        self,
        db: Session,
        engine: AIEngine,
        user: User,
        resource_identifier: str,
        style: str = "bullet",
        force_regenerate: bool = False,
    ) -> NotesResponse:
        resource = self._resource_repo.get_by_user(db, user.id, resource_identifier)
        if not resource:
            raise ResourceNotFoundError(
                f"Resource '{resource_identifier}' not found or not owned by user."
            )

        # Pre-fetch or generate summary first
        self.get_summary(db, engine, user, resource_identifier, force_regenerate=force_regenerate)

        notes_text = engine.generate_notes(
            resource.source,
            style=style,
            resource_id=resource.resource_id,
            force_regenerate=force_regenerate,
        )

        saved = self._study_repo.save_notes(db, resource.resource_id, style, notes_text)

        return NotesResponse(
            id=saved.id,
            resource_id=resource.resource_id,
            style=saved.style,
            content=saved.content,
            created_at=saved.created_at,
        )

    def get_existing_notes(
        self, db: Session, user: User, resource_identifier: str, style: str = "bullet"
    ) -> Optional[NotesResponse]:
        resource = self._resource_repo.get_by_user(db, user.id, resource_identifier)
        if not resource:
            raise ResourceNotFoundError(
                f"Resource '{resource_identifier}' not found or not owned by user."
            )
        saved = self._study_repo.get_notes(db, resource.resource_id, style)
        if not saved:
            return None
        return NotesResponse.model_validate(saved)

    def generate_quiz(
        self,
        db: Session,
        engine: AIEngine,
        user: User,
        resource_identifier: str,
        question_count: int = 5,
        difficulty: str = "medium",
        force_regenerate: bool = False,
    ) -> QuizResponse:
        resource = self._resource_repo.get_by_user(db, user.id, resource_identifier)
        if not resource:
            raise ResourceNotFoundError(
                f"Resource '{resource_identifier}' not found or not owned by user."
            )

        # Pre-fetch or generate summary first
        self.get_summary(db, engine, user, resource_identifier, force_regenerate=force_regenerate)

        quiz_questions = engine.generate_quiz(
            resource.source,
            question_count=question_count,
            difficulty=difficulty,
            resource_id=resource.resource_id,
            force_regenerate=force_regenerate,
        )

        q_dicts = [
            {
                "question": q.question,
                "options": q.options,
                "correct_answer_index": q.correct_answer_index,
                "explanation": q.explanation,
            }
            for q in quiz_questions
        ]

        saved = self._study_repo.save_quiz(
            db, resource.resource_id, difficulty, question_count, q_dicts
        )

        schemas = [QuizQuestionSchema(**qd) for qd in q_dicts]

        return QuizResponse(
            id=saved.id,
            resource_id=resource.resource_id,
            difficulty=saved.difficulty,
            question_count=saved.question_count,
            questions=schemas,
            created_at=saved.created_at,
        )

    def list_quizzes(
        self, db: Session, user: User, resource_identifier: str
    ) -> List[QuizResponse]:
        resource = self._resource_repo.get_by_user(db, user.id, resource_identifier)
        if not resource:
            raise ResourceNotFoundError(
                f"Resource '{resource_identifier}' not found or not owned by user."
            )
        quizzes = self._study_repo.get_quizzes(db, resource.resource_id)
        result: List[QuizResponse] = []
        for q in quizzes:
            try:
                q_dicts = json.loads(q.data_json)
                schemas = [QuizQuestionSchema(**qd) for qd in q_dicts]
            except Exception:
                schemas = []
            result.append(
                QuizResponse(
                    id=q.id,
                    resource_id=q.resource_id,
                    difficulty=q.difficulty,
                    question_count=q.question_count,
                    questions=schemas,
                    created_at=q.created_at,
                )
            )
        return result
