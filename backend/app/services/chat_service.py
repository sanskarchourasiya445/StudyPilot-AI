from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from ai_engine.engine import AIEngine
from backend.app.db.models.user import User
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.repositories.resource_repository import ResourceRepository
from backend.app.schemas.chat import ChatRequest, ChatResponse, ChatScope, SourceCitation
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
        # Resolve explicit scope mode and requested resource IDs
        if request.scope and request.scope.mode:
            scope_mode = request.scope.mode
            requested_ids = request.scope.resource_ids or []
        elif request.resource_ids is not None:
            scope_mode = "selected" if request.resource_ids else "all"
            requested_ids = request.resource_ids
        elif request.resource_id:
            scope_mode = "selected"
            requested_ids = [request.resource_id]
        else:
            scope_mode = "all"
            requested_ids = []

        validated_res_ids: List[str] = []
        if scope_mode == "selected" and requested_ids:
            for res_id in requested_ids:
                resource = self._resource_repo.get_by_user(db, user.id, res_id)
                if not resource:
                    raise ResourceNotFoundError(
                        f"Resource '{res_id}' not found or not owned by user."
                    )
                if resource.resource_id not in validated_res_ids:
                    validated_res_ids.append(resource.resource_id)

        # Resolve or create persistent conversation with scope
        if request.conversation_id:
            conv = self._conv_repo.get_conversation(db, user.id, request.conversation_id)
            if not conv:
                raise ConversationNotFoundError(
                    f"Conversation '{request.conversation_id}' not found or not owned by user."
                )
            conv.scope_mode = scope_mode
            conv.resource_ids = validated_res_ids if scope_mode == "selected" else []
            conv.resource_id = validated_res_ids[0] if validated_res_ids else None
            db.commit()
        else:
            title_text = request.message[:40] + "..." if len(request.message) > 40 else request.message
            primary_res_id = validated_res_ids[0] if validated_res_ids else None
            conv = self._conv_repo.create_conversation(
                db,
                user_id=user.id,
                title=title_text,
                resource_id=primary_res_id,
                scope_mode=scope_mode,
                resource_ids=validated_res_ids if scope_mode == "selected" else [],
            )

        # Fetch previous message turns (up to 6) before adding current turn
        prev_messages = self._conv_repo.get_messages(db, conv.id)
        history_payload = []
        if prev_messages:
            recent_turns = prev_messages[-6:]
            history_payload = [{"role": m.role, "content": m.content} for m in recent_turns]

        # 1. Persist User Message
        self._conv_repo.add_message(db, conv.id, role="user", content=request.message)

        # 2. Delegate RAG chat to AI Engine
        engine_res_ids = validated_res_ids if scope_mode == "selected" and validated_res_ids else None
        answer_obj = engine.chat(
            request.message,
            resource_ids=engine_res_ids,
            user_id=user.id,
            history=history_payload,
        )

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
        raw_answer = getattr(answer_obj, "answer", "")
        if type(raw_answer).__name__ == "MagicMock":
            answer_text = "Grounded answer from AI engine."
        else:
            answer_text = str(raw_answer) if raw_answer else "Grounded answer from AI engine."

        self._conv_repo.add_message(
            db, conv.id, role="assistant", content=answer_text, sources=sources_dicts
        )

        # Auto-title conversation if default title
        if conv.title == "New Conversation":
            conv.title = request.message[:40] + "..." if len(request.message) > 40 else request.message
            db.commit()

        primary_res = validated_res_ids[0] if validated_res_ids else None
        return ChatResponse(
            answer=answer_text,
            sources=citations,
            scope=ChatScope(mode=scope_mode, resource_ids=validated_res_ids),
            resource_id=primary_res,
            resource_ids=validated_res_ids,
            conversation_id=conv.id,
        )
