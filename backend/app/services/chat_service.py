from typing import List, Optional
from sqlalchemy.orm import Session

from ai_engine.engine import AIEngine
from backend.app.db.models.user import User
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.repositories.resource_repository import ResourceRepository
from backend.app.schemas.chat import ChatRequest, ChatResponse, SourceCitation
from backend.app.services.conversation_service import ConversationNotFoundError
from backend.app.services.resource_service import ResourceNotFoundError


class ChatService:
    def __init__(
        self,
        resource_repo: ResourceRepository = ResourceRepository(),
        conv_repo: ConversationRepository = ConversationRepository(),
    ) -> None:
        self._resource_repo = resource_repo
        self._conv_repo = conv_repo

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

        # Resolve or create persistent conversation
        if request.conversation_id:
            conv = self._conv_repo.get_conversation(db, user.id, request.conversation_id)
            if not conv:
                raise ConversationNotFoundError(
                    f"Conversation '{request.conversation_id}' not found or not owned by user."
                )
        else:
            title_text = request.message[:40] + "..." if len(request.message) > 40 else request.message
            conv = self._conv_repo.create_conversation(
                db, user_id=user.id, title=title_text, resource_id=target_res_id
            )

        # 1. Persist User Message
        self._conv_repo.add_message(db, conv.id, role="user", content=request.message)

        # 2. Delegate RAG chat to AI Engine
        answer_obj = engine.ask(request.message, resource_id=target_res_id)

        # 3. Format Source Citations
        citations: List[SourceCitation] = []
        sources_dicts: List[dict] = []
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

            citation = SourceCitation(
                source=source_str,
                content=content_str,
                score=score_val,
                metadata=meta_dict,
            )
            citations.append(citation)
            sources_dicts.append(citation.model_dump())

        # 4. Persist Assistant Message
        self._conv_repo.add_message(
            db, conv.id, role="assistant", content=answer_obj.answer, sources=sources_dicts
        )

        # Auto-title conversation if default title
        if conv.title == "New Conversation":
            conv.title = request.message[:40] + "..." if len(request.message) > 40 else request.message
            db.commit()

        return ChatResponse(
            answer=answer_obj.answer,
            sources=citations,
            resource_id=target_res_id,
            conversation_id=conv.id,
        )
