import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from backend.app.db.models.notes import Notes
from backend.app.db.models.quiz import Quiz
from backend.app.db.models.summary import Summary


class StudyRepository:
    @staticmethod
    def get_summary(db: Session, resource_id: str) -> Optional[Summary]:
        return (
            db.query(Summary)
            .filter(Summary.resource_id == resource_id)
            .order_by(Summary.created_at.desc())
            .first()
        )

    @staticmethod
    def save_summary(
        db: Session, resource_id: str, summary_text: str, config_hash: str
    ) -> Summary:
        existing = StudyRepository.get_summary(db, resource_id)
        if existing:
            existing.summary = summary_text
            existing.config_hash = config_hash
            db.commit()
            db.refresh(existing)
            return existing

        rec = Summary(
            resource_id=resource_id,
            summary=summary_text,
            version="1.0",
            config_hash=config_hash,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

    @staticmethod
    def get_notes(db: Session, resource_id: str, style: str = "bullet") -> Optional[Notes]:
        return (
            db.query(Notes)
            .filter(Notes.resource_id == resource_id, Notes.style == style)
            .order_by(Notes.created_at.desc())
            .first()
        )

    @staticmethod
    def save_notes(db: Session, resource_id: str, style: str, content: str) -> Notes:
        existing = StudyRepository.get_notes(db, resource_id, style)
        if existing:
            existing.content = content
            db.commit()
            db.refresh(existing)
            return existing

        rec = Notes(resource_id=resource_id, style=style, content=content)
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

    @staticmethod
    def get_quizzes(db: Session, resource_id: str) -> List[Quiz]:
        return (
            db.query(Quiz)
            .filter(Quiz.resource_id == resource_id)
            .order_by(Quiz.created_at.desc())
            .all()
        )

    @staticmethod
    def save_quiz(
        db: Session,
        resource_id: str,
        difficulty: str,
        question_count: int,
        questions: List[Dict[str, Any]],
    ) -> Quiz:
        rec = Quiz(
            resource_id=resource_id,
            difficulty=difficulty,
            question_count=question_count,
            data_json=json.dumps(questions),
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec
