from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.db.models.user import User
from backend.app.schemas.conversation import ConversationCreate, ConversationRead, MessageRead
from backend.app.services.conversation_service import ConversationNotFoundError, ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversations"])
conv_service = ConversationService()


@router.post(
    "",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation session",
    description="Creates a new conversation thread for the authenticated user, optionally scoped to a resource.",
)
def create_conversation(
    request: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationRead:
    return conv_service.create_conversation(db, current_user, request)


@router.get(
    "",
    response_model=List[ConversationRead],
    summary="List authenticated user's conversations",
    description="Returns all conversation threads owned by the user, optionally filtered by resource_id.",
)
def list_conversations(
    resource_id: Optional[str] = Query(None, description="Optional resource_id filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ConversationRead]:
    return conv_service.list_conversations(db, current_user, resource_id=resource_id)


@router.get(
    "/{conversation_id}",
    response_model=ConversationRead,
    summary="Get conversation details",
    description="Returns details for a specific conversation thread owned by the user.",
)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationRead:
    try:
        return conv_service.get_conversation(db, current_user, conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{conversation_id}/messages",
    response_model=List[MessageRead],
    summary="Get message history for a conversation",
    description="Retrieves all persistent chat messages (user and assistant turns) for a conversation.",
)
def get_conversation_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MessageRead]:
    try:
        return conv_service.get_messages(db, current_user, conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{conversation_id}",
    summary="Delete a conversation",
    description="Deletes a conversation thread and all associated persistent messages for the user.",
)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    try:
        conv_service.delete_conversation(db, current_user, conversation_id)
        return {"message": "Conversation deleted successfully", "conversation_id": conversation_id}
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
