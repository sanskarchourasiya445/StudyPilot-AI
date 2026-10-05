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
from backend.app.schemas.mastery import (
    QuizAttemptResponse,
    MasteryRecordResponse,
    KnowledgeGapResponse,
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

    def get_existing_summary(
        self, db: Session, user: User, resource_identifier: str
    ) -> Optional[SummaryResponse]:
        resource = self._resource_repo.get_by_user(db, user.id, resource_identifier)
        if not resource:
            raise ResourceNotFoundError(
                f"Resource '{resource_identifier}' not found or not owned by user."
            )
        db_summary = self._study_repo.get_summary(db, resource.resource_id)
        if not db_summary:
            return None
        return SummaryResponse(
            id=db_summary.id,
            resource_id=resource.resource_id,
            summary=db_summary.summary,
            version=db_summary.version,
            config_hash=db_summary.config_hash,
            cached=True,
            created_at=db_summary.created_at,
        )

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

    def delete_summary(
        self, db: Session, engine: AIEngine, user: User, resource_identifier: str
    ) -> bool:
        resource = self._resource_repo.get_by_user(db, user.id, resource_identifier)
        if not resource:
            raise ResourceNotFoundError(
                f"Resource '{resource_identifier}' not found or not owned by user."
            )
        if hasattr(engine, "_summary_cache"):
            engine._summary_cache.invalidate(resource.resource_id)
        return self._study_repo.delete_summary(db, resource.resource_id)

    def delete_notes(
        self, db: Session, user: User, resource_identifier: str, style: Optional[str] = None
    ) -> bool:
        resource = self._resource_repo.get_by_user(db, user.id, resource_identifier)
        if not resource:
            raise ResourceNotFoundError(
                f"Resource '{resource_identifier}' not found or not owned by user."
            )
        return self._study_repo.delete_notes(db, resource.resource_id, style=style)

    def delete_quizzes(
        self, db: Session, user: User, resource_identifier: str, quiz_id: Optional[str] = None
    ) -> bool:
        resource = self._resource_repo.get_by_user(db, user.id, resource_identifier)
        if not resource:
            raise ResourceNotFoundError(
                f"Resource '{resource_identifier}' not found or not owned by user."
            )
        return self._study_repo.delete_quizzes(db, resource.resource_id, quiz_id=quiz_id)

    def submit_quiz_attempt(
        self,
        db: Session,
        user: User,
        quiz_id: str,
        score: int,
        total_questions: int,
        topic_override: Optional[str] = None,
    ) -> QuizAttemptResponse:
        from datetime import datetime, timezone
        from backend.app.db.models.quiz import Quiz
        from backend.app.db.models.resource import Resource
        from backend.app.db.models.quiz_attempt import QuizAttempt
        from backend.app.db.models.mastery import MasteryRecord
        from backend.app.schemas.mastery import QuizAttemptResponse

        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise ResourceNotFoundError(f"Quiz '{quiz_id}' not found.")

        resource = (
            db.query(Resource)
            .filter(Resource.resource_id == quiz.resource_id, Resource.user_id == user.id)
            .first()
        )
        if not resource:
            raise ResourceNotFoundError(f"Resource for quiz '{quiz_id}' not found or not owned by user.")

        # Determine Topic Name
        if topic_override and topic_override.strip():
            topic = topic_override.strip()
        else:
            raw_name = resource.title or resource.source.split("/")[-1].split("\\")[-1]
            if raw_name.lower().endswith(".pdf"):
                raw_name = raw_name[:-4]
            topic = raw_name.strip() or "General Study"

        total_q = max(1, total_questions)
        score_val = max(0, min(score, total_q))
        percentage = round((score_val / total_q) * 100.0, 1)

        # 1. Save QuizAttempt
        attempt = QuizAttempt(
            user_id=user.id,
            quiz_id=quiz.id,
            resource_id=resource.resource_id,
            topic=topic,
            score=score_val,
            total_questions=total_q,
            percentage=percentage,
            attempted_at=datetime.now(timezone.utc),
        )
        db.add(attempt)

        # 2. Find or create MasteryRecord for (user_id, topic)
        mastery = (
            db.query(MasteryRecord)
            .filter(MasteryRecord.user_id == user.id, MasteryRecord.topic == topic)
            .first()
        )

        from backend.app.services.revision_service import calculate_next_review_at, get_review_interval

        now = datetime.now(timezone.utc)

        if not mastery:
            new_score = int(round(percentage))
            mastery = MasteryRecord(
                user_id=user.id,
                topic=topic,
                mastery_score=max(0, min(100, new_score)),
                total_questions=total_q,
                correct_answers=score_val,
                total_attempts=1,
                last_attempt_at=now,
            )
            db.add(mastery)
        else:
            # Weighted average formula: 60% historical + 40% latest quiz
            updated_score = int(round(0.6 * mastery.mastery_score + 0.4 * percentage))
            mastery.mastery_score = max(0, min(100, updated_score))
            mastery.total_questions += total_q
            mastery.correct_answers += score_val
            mastery.total_attempts += 1
            mastery.last_attempt_at = now

        # Phase 4: Calculate Spaced-Repetition Revision Schedule
        interval_days = get_review_interval(mastery.mastery_score)
        mastery.next_review_at = calculate_next_review_at(mastery.mastery_score, now)
        mastery.last_reviewed_at = now

        db.commit()
        db.refresh(attempt)
        db.refresh(mastery)

        return QuizAttemptResponse(
            id=attempt.id,
            quiz_id=quiz.id,
            resource_id=resource.resource_id,
            topic=topic,
            score=score_val,
            total_questions=total_q,
            percentage=percentage,
            attempted_at=attempt.attempted_at,
            mastery_score=mastery.mastery_score,
            mastery_status=mastery.status,
            recommendation=mastery.recommendation,
            next_review_at=mastery.next_review_at,
            review_interval_days=interval_days,
        )

    def get_user_mastery(self, db: Session, user: User) -> List[Any]:
        from backend.app.db.models.mastery import MasteryRecord
        from backend.app.schemas.mastery import MasteryRecordResponse

        records = (
            db.query(MasteryRecord)
            .filter(MasteryRecord.user_id == user.id)
            .order_by(MasteryRecord.last_attempt_at.desc())
            .all()
        )
        return [
            MasteryRecordResponse(
                id=r.id,
                topic=r.topic,
                mastery_score=r.mastery_score,
                status=r.status,
                total_questions=r.total_questions,
                correct_answers=r.correct_answers,
                total_attempts=r.total_attempts,
                last_attempt_at=r.last_attempt_at,
                recommendation=r.recommendation,
            )
            for r in records
        ]

    def get_user_knowledge_gaps(self, db: Session, user: User) -> Any:
        from backend.app.schemas.mastery import KnowledgeGapResponse

        all_records = self.get_user_mastery(db, user)
        gaps = [r for r in all_records if r.mastery_score < 70]
        mastered = [r for r in all_records if r.mastery_score >= 85]

        return KnowledgeGapResponse(
            total_topics=len(all_records),
            gaps_count=len(gaps),
            mastered_count=len(mastered),
            gaps=gaps,
            all_mastery=all_records,
        )

    def get_recommended_difficulty_for_topic(
        self, db: Session, user: User, topic_name: str
    ) -> Any:
        from backend.app.db.models.mastery import MasteryRecord
        from backend.app.services.difficulty_service import get_recommended_difficulty
        from backend.app.schemas.mastery import DifficultyRecommendationResponse

        topic = topic_name.strip()
        record = (
            db.query(MasteryRecord)
            .filter(MasteryRecord.user_id == user.id, MasteryRecord.topic == topic)
            .first()
        )

        score = record.mastery_score if record else None
        difficulty, reason = get_recommended_difficulty(score)

        return DifficultyRecommendationResponse(
            topic=topic,
            mastery_score=score,
            recommended_difficulty=difficulty,
            reason=reason,
        )
