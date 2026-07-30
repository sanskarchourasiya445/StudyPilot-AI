import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from backend.app.db.models.conversation import Conversation
from backend.app.db.models.message import Message


class ConversationRepository:
    @staticmethod
    def create_conversation(
        db: Session,
        user_id: str,
        title: Optional[str] = None,
        resource_id: Optional[str] = None,
    ) -> Conversation:
        conv = Conversation(
            user_id=user_id,
            resource_id=resource_id,
            title=title.strip() if title else "New Conversation",
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def get_conversation(
        db: Session, user_id: str, conversation_id: str
    ) -> Optional[Conversation]:
        return (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id, Conversation.id == conversation_id)
            .first()
        )

    @staticmethod
    def list_conversations(
        db: Session, user_id: str, resource_id: Optional[str] = None
    ) -> List[Conversation]:
        query = db.query(Conversation).filter(Conversation.user_id == user_id)
        if resource_id:
            query = query.filter(Conversation.resource_id == resource_id)
        return query.order_by(Conversation.updated_at.desc()).all()

    @staticmethod
    def delete_conversation(db: Session, conversation: Conversation) -> None:
        db.delete(conversation)
        db.commit()

    @staticmethod
    def add_message(
        db: Session,
        conversation_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Message:
        sources_str = json.dumps(sources) if sources else None
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources_json=sources_str,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def get_messages(db: Session, conversation_id: str) -> List[Message]:
        return (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )
