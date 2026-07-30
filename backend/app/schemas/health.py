from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    backend: str = Field(..., json_schema_extra={"example": "online"})
    database: str = Field(..., json_schema_extra={"example": "connected"})
    ai_engine: Dict[str, Any] = Field(
        ...,
        json_schema_extra={
            "example": {
                "initialized": True,
                "vector_store_reachable": True,
                "embedding_model_loaded": True,
                "llm_configured": True,
            }
        },
    )
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    engine_version: Optional[str] = Field(None, json_schema_extra={"example": "1.1.0"})
