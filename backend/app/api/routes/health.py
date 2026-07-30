from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ai_engine.engine import AIEngine
from backend.app.api.deps import get_db, get_engine
from backend.app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API & System Health",
    description="Check backend API, database connectivity, and AI Engine status.",
)
def check_health(
    db: Session = Depends(get_db),
    engine: AIEngine = Depends(get_engine),
) -> HealthResponse:
    # Check Database Connectivity
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"disconnected: {exc}"

    # Check AI Engine Health
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

    overall_status = (
        "healthy"
        if db_status == "connected" and ai_engine_dict.get("initialized")
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
