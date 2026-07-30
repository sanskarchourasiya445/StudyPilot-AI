import logging
from typing import Optional
from ai_engine.engine import AIEngine
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

_ai_engine_instance: Optional[AIEngine] = None


def get_ai_engine() -> AIEngine:
    """Return the application-wide singleton AIEngine instance.

    Reuses the existing initialized instance rather than re-creating/re-initializing
    it on every HTTP request.
    """
    global _ai_engine_instance
    if _ai_engine_instance is None:
        logger.info("Initializing singleton AIEngine instance...")
        api_key = settings.GEMINI_API_KEY or None
        engine = AIEngine(gemini_api_key=api_key)
        engine.initialize()
        _ai_engine_instance = engine
        logger.info("Singleton AIEngine initialized successfully.")
    return _ai_engine_instance


def set_ai_engine(engine: AIEngine) -> None:
    """Explicitly set or mock the singleton engine instance (useful for testing)."""
    global _ai_engine_instance
    _ai_engine_instance = engine


def reset_ai_engine() -> None:
    """Reset the singleton instance reference."""
    global _ai_engine_instance
    _ai_engine_instance = None
