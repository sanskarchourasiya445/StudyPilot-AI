import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.middleware import setup_exception_handlers
from backend.app.api.routes import auth, chat, conversations, health, mastery, resources, revision, study
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.db.base import Base
from backend.app.db.session import engine

logger = logging.getLogger(__name__)


def ensure_db_schema():
    """Ensure database tables exist when running in pytest test execution."""
    if os.getenv("PYTEST_CURRENT_TEST"):
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            logger.warning(f"Database schema initialization warning: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    setup_logging()
    logger.info("Starting StudyPilot API backend...")
    ensure_db_schema()
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

# Register Exception Handlers
setup_exception_handlers(app)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    origins = [str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include Routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(resources.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(study.router, prefix=settings.API_V1_STR)
app.include_router(conversations.router, prefix=settings.API_V1_STR)
app.include_router(mastery.router, prefix=settings.API_V1_STR)
app.include_router(revision.router, prefix=settings.API_V1_STR)


@app.get("/health", include_in_schema=False)
def liveness_check():
    """Lightweight liveness probe for container health checks."""
    return {"status": "ok", "service": "studypilot"}


# Production Frontend SPA Static Serving
frontend_dist_dir = Path(settings.FRONTEND_DIST_DIR).resolve()
if not frontend_dist_dir.exists():
    alt_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if alt_dist.exists():
        frontend_dist_dir = alt_dist


@app.get("/", include_in_schema=False)
def root_endpoint(request: Request):
    accept = request.headers.get("accept", "")
    # Serve React SPA index.html to web browsers; JSON metadata to API clients/tests
    if "text/html" in accept and frontend_dist_dir.exists() and (frontend_dist_dir / "index.html").exists():
        return FileResponse(str(frontend_dist_dir / "index.html"))
    return {
        "message": "Welcome to StudyPilot API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }


if frontend_dist_dir.exists() and (frontend_dist_dir / "index.html").exists():
    assets_dir = frontend_dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if not full_path:
            return FileResponse(str(frontend_dist_dir / "index.html"))
        if full_path.startswith(("api", "docs", "redoc", "openapi.json")):
            raise HTTPException(status_code=404, detail="Not Found")

        file_path = frontend_dist_dir / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist_dir / "index.html"))
