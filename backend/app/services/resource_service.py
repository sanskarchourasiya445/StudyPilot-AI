import os
import shutil
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from ai_engine.engine import AIEngine, EngineError, ResourceManagementError
from backend.app.db.models.resource import Resource
from backend.app.db.models.user import User
from backend.app.repositories.resource_repository import ResourceRepository
from backend.app.schemas.resource import YouTubeIngestRequest

UPLOAD_DIR = os.path.join(os.getcwd(), "data", "uploads")


class ResourceNotFoundError(Exception):
    """Raised when a requested resource is not found or not owned by the user."""


class ResourceService:
    def __init__(self, resource_repo: ResourceRepository = ResourceRepository()) -> None:
        self._resource_repo = resource_repo

    def ingest_pdf(
        self,
        db: Session,
        engine: AIEngine,
        user: User,
        upload_file: UploadFile,
    ) -> Resource:
        filename = upload_file.filename or "file.pdf"
        if not filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are supported for file upload.")

        user_upload_dir = os.path.join(UPLOAD_DIR, user.id)
        os.makedirs(user_upload_dir, exist_ok=True)
        file_path = os.path.join(user_upload_dir, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        try:
            ingestion_res = engine.ingest(file_path)
            meta = {
                "original_filename": filename,
                "pages": ingestion_res.pages_or_segments,
                "chunks": ingestion_res.chunks_created,
            }
            return self._resource_repo.create(
                db=db,
                user_id=user.id,
                resource_id=ingestion_res.resource_id,
                source=file_path,
                source_type="pdf",
                title=filename,
                status="ready",
                metadata=meta,
            )
        except Exception as exc:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            raise exc

    def ingest_youtube(
        self,
        db: Session,
        engine: AIEngine,
        user: User,
        request: YouTubeIngestRequest,
    ) -> Resource:
        ingestion_res = engine.ingest(request.url)
        meta = {
            "url": request.url,
            "segments": ingestion_res.pages_or_segments,
            "chunks": ingestion_res.chunks_created,
        }
        return self._resource_repo.create(
            db=db,
            user_id=user.id,
            resource_id=ingestion_res.resource_id,
            source=request.url,
            source_type="youtube",
            title=request.title or request.url,
            status="ready",
            metadata=meta,
        )

    def list_resources(self, db: Session, user: User) -> List[Resource]:
        return self._resource_repo.list_by_user(db, user.id)

    def get_resource(
        self, db: Session, user: User, resource_identifier: str
    ) -> Resource:
        resource = self._resource_repo.get_by_user(db, user.id, resource_identifier)
        if not resource:
            raise ResourceNotFoundError(
                f"Resource '{resource_identifier}' not found for user."
            )
        return resource

    def delete_resource(
        self, db: Session, engine: AIEngine, user: User, resource_identifier: str
    ) -> None:
        resource = self.get_resource(db, user, resource_identifier)

        # 1. Delete from AI Engine vector store & cache
        try:
            engine.delete_resource(resource.resource_id)
        except Exception as exc:
            # Log error but proceed if chunks were already cleaned up
            pass

        # 2. If source file exists on disk, remove it
        if resource.source_type == "pdf" and os.path.exists(resource.source):
            try:
                os.remove(resource.source)
            except Exception:
                pass

        # 3. Delete DB record
        self._resource_repo.delete(db, resource)
