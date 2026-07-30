from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.db.models.conversation import Conversation
from backend.app.db.models.user import User
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.schemas.chat import SourceCitation
from backend.app.schemas.conversation import ConversationCreate, ConversationRead, MessageRead


class ConversationNotFoundError(Exception):
    """Raised when a requested conversation is not found or not owned by the user."""


class ConversationService:
    def __init__(self, conv_repo: ConversationRepository = ConversationRepository()) -> None:
        self._conv_repo = conv_repo

    def create_conversation(
        self, db: Session, user: User, request: ConversationCreate
    ) -> ConversationRead:
        conv = self._conv_repo.create_conversation(
            db, user_id=user.id, title=request.title, resource_id=request.resource_id
        )
        return ConversationRead(
            id=conv.id,
            user_id=conv.user_id,
            resource_id=conv.resource_id,
            title=conv.title,
            message_count=0,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )

    def list_conversations(
        self, db: Session, user: User, resource_id: Optional[str] = None
    ) -> List[ConversationRead]:
        convs = self._conv_repo.list_conversations(db, user.id, resource_id=resource_id)
        result: List[ConversationRead] = []
        for c in convs:
            msg_cnt = len(c.messages)
            result.append(
                ConversationRead(
                    id=c.id,
                    user_id=c.user_id,
                    resource_id=c.resource_id,
                    title=c.title,
                    message_count=msg_cnt,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
            )
        return result

    def get_conversation_model(
        self, db: Session, user: User, conversation_id: str
    ) -> Conversation:
        conv = self._conv_repo.get_conversation(db, user.id, conversation_id)
        if not conv:
            raise ConversationNotFoundError(
                f"Conversation '{conversation_id}' not found or not owned by user."
            )
        return conv

    def get_conversation(
        self, db: Session, user: User, conversation_id: str
    ) -> ConversationRead:
        conv = self.get_conversation_model(db, user, conversation_id)
        return ConversationRead(
            id=conv.id,
            user_id=conv.user_id,
            resource_id=conv.resource_id,
            title=conv.title,
            message_count=len(conv.messages),
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )

    def get_messages(
        self, db: Session, user: User, conversation_id: str
    ) -> List[MessageRead]:
        # Verifies user ownership
        conv = self.get_conversation_model(db, user, conversation_id)
        messages = self._conv_repo.get_messages(db, conv.id)

        result: List[MessageRead] = []
        for m in messages:
            sources_schemas = [SourceCitation(**sd) for sd in m.sources_list]
            result.append(
                MessageRead(
                    id=m.id,
                    conversation_id=m.conversation_id,
                    role=m.role,
                    content=m.content,
                    sources=sources_schemas,
                    created_at=m.created_at,
                )
            )
        return result

    def delete_conversation(
        self, db: Session, user: User, conversation_id: str
    ) -> None:
        conv = self.get_conversation_model(db, user, conversation_id)
        self._conv_repo.delete_conversation(db, conv)
