from typing import List, Optional
from sqlalchemy.orm import Session

from ai_engine.engine import AIEngine
from backend.app.db.models.user import User
from backend.app.repositories.resource_repository import ResourceRepository
from backend.app.schemas.chat import ChatRequest, ChatResponse, SourceCitation
from backend.app.services.resource_service import ResourceNotFoundError


class ChatService:
    def __init__(self, resource_repo: ResourceRepository = ResourceRepository()) -> None:
        self._resource_repo = resource_repo

    def chat(
        self,
        db: Session,
        engine: AIEngine,
        user: User,
        request: ChatRequest,
    ) -> ChatResponse:
        target_res_id: Optional[str] = None

        if request.resource_id:
            resource = self._resource_repo.get_by_user(db, user.id, request.resource_id)
            if not resource:
                raise ResourceNotFoundError(
                    f"Resource '{request.resource_id}' not found or not owned by user."
                )
            target_res_id = resource.resource_id

        # Delegate RAG chat to AI Engine
        answer_obj = engine.ask(request.message, resource_id=target_res_id)

        citations: List[SourceCitation] = []
        for s in getattr(answer_obj, "sources", []):
            if hasattr(s, "page_content"):  # LangChain Document
                content_str = s.page_content
                meta_dict = getattr(s, "metadata", {}) or {}
                source_str = meta_dict.get("source", "") or meta_dict.get("original_filename", "")
                score_val = meta_dict.get("score", 0.0)
            elif isinstance(s, dict):
                content_str = s.get("content", "")
                meta_dict = s.get("metadata", {}) or {}
                source_str = s.get("source", "") or meta_dict.get("source", "")
                score_val = float(s.get("score", 0.0))
            else:
                content_str = getattr(s, "content", str(s))
                meta_dict = getattr(s, "metadata", {}) or {}
                source_str = getattr(s, "source", "")
                score_val = getattr(s, "score", 0.0)

            citations.append(
                SourceCitation(
                    source=source_str,
                    content=content_str,
                    score=score_val,
                    metadata=meta_dict,
                )
            )

        return ChatResponse(
            answer=answer_obj.answer,
            sources=citations,
            resource_id=target_res_id,
            conversation_id=request.conversation_id,
        )
