import os
import shutil
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from ai_engine.engine import AIEngine, EngineError, ResourceManagementError
from backend.app.db.models.resource import Resource
from backend.app.db.models.user import User
from backend.app.db.models.summary import Summary
from backend.app.db.models.notes import Notes
from backend.app.db.models.quiz import Quiz
from backend.app.repositories.resource_repository import ResourceRepository
from backend.app.schemas.resource import ResourceRead, YouTubeIngestRequest

UPLOAD_DIR = os.getenv("UPLOAD_DIR") or os.path.join(os.getcwd(), "data", "uploads")
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_MB", 50)) * 1024 * 1024


class ResourceNotFoundError(Exception):
    """Raised when a requested resource is not found or not owned by the user."""


class ResourceService:
    def __init__(self, resource_repo: ResourceRepository = ResourceRepository()) -> None:
        self._resource_repo = resource_repo

    def _enrich_resource(self, db: Session, resource: Resource) -> ResourceRead:
        dto = ResourceRead.model_validate(resource)
        meta = resource.metadata_dict or {}

        # Fallback metadata parsing if chunk_count or page_count were 0
        if dto.page_count == 0:
            dto.page_count = int(
                meta.get("pages")
                or meta.get("segments")
                or meta.get("pages_or_segments")
                or meta.get("page_count")
                or 0
            )
        if dto.chunk_count == 0:
            dto.chunk_count = int(
                meta.get("chunks")
                or meta.get("chunks_created")
                or meta.get("chunk_count")
                or 0
            )

        # Calculate file_size for PDFs if missing
        if resource.source_type == "pdf" and not dto.file_size and os.path.exists(resource.source):
            try:
                dto.file_size = os.path.getsize(resource.source)
            except Exception:
                pass

        dto.has_summary = (
            db.query(Summary).filter(Summary.resource_id == resource.resource_id).first()
            is not None
        )
        dto.has_notes = (
            db.query(Notes).filter(Notes.resource_id == resource.resource_id).first()
            is not None
        )
        dto.has_quiz = (
            db.query(Quiz).filter(Quiz.resource_id == resource.resource_id).first()
            is not None
        )
        return dto

    def ingest_pdf(
        self,
        db: Session,
        engine: AIEngine,
        user: User,
        upload_file: UploadFile,
    ) -> ResourceRead:
        raw_filename = upload_file.filename or "file.pdf"
        filename = os.path.basename(raw_filename)
        if not filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are supported for file upload.")

        # Validate file size against maximum permitted threshold
        upload_file.file.seek(0, os.SEEK_END)
        actual_size = upload_file.file.tell()
        upload_file.file.seek(0)
        if actual_size > MAX_UPLOAD_SIZE_BYTES:
            limit_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            raise ValueError(f"File size exceeds maximum permitted limit ({limit_mb} MB).")

        user_upload_dir = os.path.join(UPLOAD_DIR, user.id)
        os.makedirs(user_upload_dir, exist_ok=True)
        file_path = os.path.join(user_upload_dir, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        try:
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            ingestion_res = engine.ingest(file_path, user_id=user.id)
            meta = {
                "original_filename": filename,
                "pages": ingestion_res.pages_or_segments,
                "page_count": ingestion_res.pages_or_segments,
                "chunks": ingestion_res.chunks_created,
                "chunk_count": ingestion_res.chunks_created,
                "file_size": file_size,
            }
            rec = self._resource_repo.create(
                db=db,
                user_id=user.id,
                resource_id=ingestion_res.resource_id,
                source=file_path,
                source_type="pdf",
                title=filename,
                status="ready",
                metadata=meta,
            )
            return self._enrich_resource(db, rec)
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
    ) -> ResourceRead:
        ingestion_res = engine.ingest(request.url, user_id=user.id)
        meta = {
            "url": request.url,
            "segments": ingestion_res.pages_or_segments,
            "page_count": ingestion_res.pages_or_segments,
            "chunks": ingestion_res.chunks_created,
            "chunk_count": ingestion_res.chunks_created,
        }
        rec = self._resource_repo.create(
            db=db,
            user_id=user.id,
            resource_id=ingestion_res.resource_id,
            source=request.url,
            source_type="youtube",
            title=request.title or request.url,
            status="ready",
            metadata=meta,
        )
        return self._enrich_resource(db, rec)

    def list_resources(self, db: Session, user: User) -> List[ResourceRead]:
        resources = self._resource_repo.list_by_user(db, user.id)
        return [self._enrich_resource(db, r) for r in resources]

    def get_resource(
        self, db: Session, user: User, resource_identifier: str
    ) -> ResourceRead:
        resource = self._resource_repo.get_by_user(db, user.id, resource_identifier)
        if not resource:
            raise ResourceNotFoundError(
                f"Resource '{resource_identifier}' not found for user."
            )
        return self._enrich_resource(db, resource)

    def delete_resource(
        self, db: Session, engine: AIEngine, user: User, resource_identifier: str
    ) -> None:
        resource = self._resource_repo.get_by_user(db, user.id, resource_identifier)
        if not resource:
            raise ResourceNotFoundError(
                f"Resource '{resource_identifier}' not found for user."
            )

        # 1. Delete from AI Engine vector store & cache
        try:
            engine.delete_resource(resource.resource_id)
        except Exception as exc:
            pass

        # 2. If source file exists on disk, remove it
        if resource.source_type == "pdf" and os.path.exists(resource.source):
            try:
                os.remove(resource.source)
            except Exception:
                pass

        # 3. Delete DB record
        self._resource_repo.delete(db, resource)
