from typing import TYPE_CHECKING
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.ai.engine_provider import get_existing_ai_engine
from backend.app.api.deps import get_db
from backend.app.schemas.health import HealthResponse

if TYPE_CHECKING:
    from ai_engine.engine import AIEngine

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API & System Health",
    description="Check backend API, database connectivity, and AI Engine status.",
)
def check_health(
    db: Session = Depends(get_db),
) -> HealthResponse:
    # Check Database Connectivity
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"disconnected: {exc}"

    # Check AI Engine Health without forcing eager initialization
    engine = get_existing_ai_engine()
    if engine is not None:
        try:
            engine_health_obj = engine.health()
            ai_engine_dict = {
                "initialized": engine_health_obj.initialized,
                "vector_store_reachable": engine_health_obj.vector_store_reachable,
                "embedding_model_loaded": engine_health_obj.embedding_model_loaded,
                "llm_configured": engine_health_obj.llm_configured,
            }
            engine_ver = engine.version()
        except Exception as exc:
            ai_engine_dict = {"initialized": False, "error": str(exc)}
            engine_ver = "unknown"
    else:
        ai_engine_dict = {
            "initialized": False,
            "status": "standby",
            "vector_store_reachable": False,
            "embedding_model_loaded": False,
            "llm_configured": False,
        }
        engine_ver = "standby"

    overall_status = (
        "healthy"
        if db_status == "connected"
        and (ai_engine_dict.get("initialized") or ai_engine_dict.get("status") == "standby")
        else "degraded"
    )

    return HealthResponse(
        status=overall_status,
        backend="online",
        database=db_status,
        ai_engine=ai_engine_dict,
        version="1.0.0",
        engine_version=engine_ver,
    )
