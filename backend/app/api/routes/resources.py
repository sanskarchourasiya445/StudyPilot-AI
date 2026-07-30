from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ai_engine.engine import AIEngine
from backend.app.api.deps import get_current_user, get_db, get_engine
from backend.app.db.models.user import User
from backend.app.schemas.resource import ResourceRead, YouTubeIngestRequest
from backend.app.services.resource_service import ResourceNotFoundError, ResourceService

router = APIRouter(prefix="/resources", tags=["Resources"])
resource_service = ResourceService()


@router.post(
    "/pdf",
    response_model=ResourceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a PDF document",
    description="Ingests a PDF file into the vector store and associates it with the authenticated user.",
)
def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    engine: AIEngine = Depends(get_engine),
    current_user: User = Depends(get_current_user),
) -> ResourceRead:
    try:
        resource = resource_service.ingest_pdf(db, engine, current_user, file)
        return resource
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest PDF: {exc}",
        ) from exc


@router.post(
    "/youtube",
    response_model=ResourceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a YouTube lecture video",
    description="Ingests a YouTube video transcript/captions into the vector store for the authenticated user.",
)
def ingest_youtube(
    request: YouTubeIngestRequest,
    db: Session = Depends(get_db),
    engine: AIEngine = Depends(get_engine),
    current_user: User = Depends(get_current_user),
) -> ResourceRead:
    try:
        resource = resource_service.ingest_youtube(db, engine, current_user, request)
        return resource
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to ingest YouTube URL: {exc}",
        ) from exc


@router.get(
    "",
    response_model=List[ResourceRead],
    summary="List authenticated user's resources",
    description="Returns all ingested resources belonging to the authenticated user.",
)
def list_resources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ResourceRead]:
    return resource_service.list_resources(db, current_user)


@router.get(
    "/{resource_id}",
    response_model=ResourceRead,
    summary="Get resource details",
    description="Returns metadata and ingestion status for a specific resource owned by the user.",
)
def get_resource(
    resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResourceRead:
    try:
        return resource_service.get_resource(db, current_user, resource_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{resource_id}",
    summary="Delete a resource",
    description="Deletes a resource and its vector store chunks for the authenticated user.",
)
def delete_resource(
    resource_id: str,
    db: Session = Depends(get_db),
    engine: AIEngine = Depends(get_engine),
    current_user: User = Depends(get_current_user),
) -> dict:
    try:
        resource_service.delete_resource(db, engine, current_user, resource_id)
        return {"message": "Resource deleted successfully", "resource_id": resource_id}
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete resource: {exc}",
        ) from exc
