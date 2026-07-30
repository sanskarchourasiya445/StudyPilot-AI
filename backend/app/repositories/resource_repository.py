import json
from typing import Any, Dict, List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from backend.app.db.models.resource import Resource


class ResourceRepository:
    @staticmethod
    def create(
        db: Session,
        user_id: str,
        resource_id: str,
        source: str,
        source_type: str,
        title: Optional[str] = None,
        workspace_id: Optional[str] = None,
        status: str = "ready",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Resource:
        metadata_str = json.dumps(metadata) if metadata else None
        res = Resource(
            user_id=user_id,
            resource_id=resource_id,
            source=source,
            source_type=source_type,
            title=title,
            workspace_id=workspace_id,
            status=status,
            metadata_json=metadata_str,
        )
        db.add(res)
        db.commit()
        db.refresh(res)
        return res

    @staticmethod
    def get_by_user(db: Session, user_id: str, resource_identifier: str) -> Optional[Resource]:
        """Fetch resource by either DB PK `id` OR AI Engine `resource_id`, strictly scoped to `user_id`."""
        return (
            db.query(Resource)
            .filter(
                Resource.user_id == user_id,
                or_(
                    Resource.id == resource_identifier,
                    Resource.resource_id == resource_identifier,
                ),
            )
            .first()
        )

    @staticmethod
    def list_by_user(db: Session, user_id: str) -> List[Resource]:
        return (
            db.query(Resource)
            .filter(Resource.user_id == user_id)
            .order_by(Resource.created_at.desc())
            .all()
        )

    @staticmethod
    def delete(db: Session, resource: Resource) -> None:
        db.delete(resource)
        db.commit()
