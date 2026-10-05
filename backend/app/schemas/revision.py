from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RevisionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    topic: str
    resource_id: Optional[str] = None
    mastery_score: int
    mastery_status: str
    status: str  # "Scheduled", "Due", "Not Scheduled"
    next_review_at: Optional[datetime] = None
    review_interval_days: int
    last_attempt_at: datetime
    recommendation: str
