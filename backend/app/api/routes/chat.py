from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ai_engine.engine import AIEngine, EngineError
from backend.app.api.deps import get_current_user, get_db, get_engine
from backend.app.db.models.user import User
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.chat_service import ChatService, ResourceNotFoundError

router = APIRouter(tags=["Chat"])
chat_service = ChatService()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with RAG Knowledge Base",
    description="Ask a question across the user's workspace or restricted to a specific resource.",
)
def chat_with_rag(
    request: ChatRequest,
    db: Session = Depends(get_db),
    engine: AIEngine = Depends(get_engine),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    try:
        return chat_service.chat(db, engine, current_user, request)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Engine Chat Failure: {exc}",
        ) from exc
