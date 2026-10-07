import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from ai_engine.utils.exceptions import (
    EngineError,
    ResourceManagementError,
    SearchError,
)
from backend.app.services.conversation_service import ConversationNotFoundError
from backend.app.services.resource_service import ResourceNotFoundError

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ResourceNotFoundError)
    async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": str(exc),
                "error_type": "ResourceNotFound",
                "status_code": status.HTTP_404_NOT_FOUND,
            },
        )

    @app.exception_handler(ConversationNotFoundError)
    async def conversation_not_found_handler(
        request: Request, exc: ConversationNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": str(exc),
                "error_type": "ConversationNotFound",
                "status_code": status.HTTP_404_NOT_FOUND,
            },
        )

    @app.exception_handler(SearchError)
    async def search_error_handler(request: Request, exc: SearchError) -> JSONResponse:
        logger.error(f"Search Error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": f"Search failed: {exc}",
                "error_type": "SearchError",
                "status_code": status.HTTP_400_BAD_REQUEST,
            },
        )

    @app.exception_handler(ResourceManagementError)
    async def resource_management_error_handler(
        request: Request, exc: ResourceManagementError
    ) -> JSONResponse:
        logger.error(f"Resource Management Error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": str(exc),
                "error_type": "ResourceManagementError",
                "status_code": status.HTTP_400_BAD_REQUEST,
            },
        )

    @app.exception_handler(EngineError)
    async def engine_error_handler(request: Request, exc: EngineError) -> JSONResponse:
        logger.error(f"AI Engine Failure: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": f"AI Engine internal error: {exc}",
                "error_type": "EngineError",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled Server Exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred. Please contact system administrator.",
                "error_type": "InternalServerError",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
        )
