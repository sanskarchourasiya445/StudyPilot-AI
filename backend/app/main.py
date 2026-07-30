import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import health
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.db.base import Base
from backend.app.db.session import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    setup_logging()
    logger.info("Starting StudyPilot API backend...")
    
    # Ensure database tables exist (Phase 1 local setup / fallback)
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Shutdown actions
    logger.info("Shutting down StudyPilot API backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include Routers
app.include_router(health.router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
def root_redirect():
    return {"message": "Welcome to StudyPilot API", "docs": "/docs", "health": f"{settings.API_V1_STR}/health"}
