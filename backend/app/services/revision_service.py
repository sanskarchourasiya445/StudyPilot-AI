from datetime import datetime, timedelta, timezone
from typing import Optional


def get_review_interval(mastery_score: int) -> int:
    """
    Deterministic spaced-repetition interval rules based on topic mastery score:
    - 0-39% mastery   -> 1 day
    - 40-69% mastery  -> 3 days
    - 70-84% mastery  -> 7 days
    - 85-100% mastery -> 14 days
    """
    score = max(0, min(100, int(mastery_score)))
    if score < 40:
        return 1
    elif score < 70:
        return 3
    elif score < 85:
        return 7
    else:
        return 14


def calculate_next_review_at(
    mastery_score: int, base_time: Optional[datetime] = None
) -> datetime:
    """
    Calculates next review timestamp = base_time + timedelta(days=review_interval)
    """
    if base_time is None:
        base_time = datetime.now(timezone.utc)
    interval_days = get_review_interval(mastery_score)
    return base_time + timedelta(days=interval_days)


def get_revision_status(
    next_review_at: Optional[datetime], current_time: Optional[datetime] = None
) -> str:
    """
    Determines dynamic revision status:
    - next_review_at is None         -> "Not Scheduled"
    - current_time < next_review_at  -> "Scheduled"
    - current_time >= next_review_at -> "Due"
    """
    if next_review_at is None:
        return "Not Scheduled"

    if current_time is None:
        current_time = datetime.now(timezone.utc)

    # Ensure tz-awareness compatibility
    if next_review_at.tzinfo is None:
        next_review_at = next_review_at.replace(tzinfo=timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    if current_time >= next_review_at:
        return "Due"
    return "Scheduled"
