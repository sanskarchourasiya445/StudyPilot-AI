from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.db.models.user import User
from backend.app.db.models.mastery import MasteryRecord
from backend.app.db.models.resource import Resource
from backend.app.schemas.revision import RevisionItemResponse
from backend.app.services.revision_service import get_revision_status, get_review_interval

router = APIRouter(prefix="/revision", tags=["Revision & Spaced Repetition"])


def _build_revision_response(record: MasteryRecord, resource_id: Optional[str] = None) -> RevisionItemResponse:
    now = datetime.now(timezone.utc)
    rev_status = get_revision_status(record.next_review_at, now)
    interval = get_review_interval(record.mastery_score)

    return RevisionItemResponse(
        id=record.id,
        topic=record.topic,
        resource_id=resource_id,
        mastery_score=record.mastery_score,
        mastery_status=record.status,
        status=rev_status,
        next_review_at=record.next_review_at,
        review_interval_days=interval,
        last_attempt_at=record.last_attempt_at,
        recommendation=record.recommendation,
    )


@router.get(
    "",
    response_model=List[RevisionItemResponse],
    summary="Get complete revision schedule for current user",
)
def get_revision_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[RevisionItemResponse]:
    records = (
        db.query(MasteryRecord)
        .filter(MasteryRecord.user_id == current_user.id)
        .order_by(MasteryRecord.last_attempt_at.desc())
        .all()
    )

    # Map topics to resource_ids for direct navigation
    resources = db.query(Resource).filter(Resource.user_id == current_user.id).all()
    topic_res_map = {}
    for r in resources:
        clean_name = r.title or r.source.split("/")[-1].split("\\")[-1]
        if clean_name.lower().endswith(".pdf"):
            clean_name = clean_name[:-4]
        norm = clean_name.strip().lower().replace("_", " ")
        topic_res_map[norm] = r.resource_id
        topic_res_map[clean_name.strip()] = r.resource_id

    result: List[RevisionItemResponse] = []
    for rec in records:
        norm_rec_topic = rec.topic.strip().lower().replace("_", " ")
        res_id = topic_res_map.get(rec.topic) or topic_res_map.get(norm_rec_topic)
        if not res_id and resources:
            res_id = resources[0].resource_id
        result.append(_build_revision_response(rec, resource_id=res_id))

    return result


@router.get(
    "/due",
    response_model=List[RevisionItemResponse],
    summary="Get revision topics that are currently due for review",
)
def get_due_revisions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[RevisionItemResponse]:
    all_schedule = get_revision_schedule(db, current_user)
    return [r for r in all_schedule if r.status == "Due"]


@router.get(
    "/upcoming",
    response_model=List[RevisionItemResponse],
    summary="Get upcoming revision topics ordered by review date",
)
def get_upcoming_revisions(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[RevisionItemResponse]:
    all_schedule = get_revision_schedule(db, current_user)
    scheduled = [r for r in all_schedule if r.next_review_at is not None]
    scheduled.sort(key=lambda x: x.next_review_at)
    return scheduled[:limit]
