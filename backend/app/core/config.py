import os
from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    PROJECT_NAME: str = "StudyPilot API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 10000

    # CORS
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database (Neon / PostgreSQL)
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/studypilot"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+psycopg2://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+"):
                return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    # JWT Authentication
    JWT_SECRET: str = "studypilot_dev_secret_key_change_in_production_32chars"

    @field_validator("JWT_SECRET", mode="before")
    @classmethod
    def assemble_jwt_secret(cls, v: str) -> str:
        if not v or v == "studypilot_dev_secret_key_change_in_production_32chars":
            import os
            alt = os.getenv("SECRET_KEY")
            if alt:
                return alt
        return v

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AI Engine
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"

    # Storage Paths & Limits
    CHROMA_PERSIST_DIRECTORY: str = "data/chroma_db"
    UPLOAD_DIR: str = "data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    FRONTEND_DIST_DIR: str = "frontend/dist"

    @property
    def resolved_upload_dir(self) -> Path:
        posix_val = self.UPLOAD_DIR.replace("\\", "/").strip()
        if posix_val.startswith("/data/"):
            sub = posix_val.removeprefix("/data/")
            if not (os.path.exists("/data") and os.access("/data", os.W_OK)):
                return (PROJECT_ROOT / "data" / sub).resolve()
        p = Path(self.UPLOAD_DIR)
        if not p.is_absolute() and not posix_val.startswith("/"):
            return (PROJECT_ROOT / p).resolve()
        return p.resolve()

    @property
    def resolved_chroma_dir(self) -> Path:
        posix_val = self.CHROMA_PERSIST_DIRECTORY.replace("\\", "/").strip()
        if posix_val.startswith("/data/"):
            sub = posix_val.removeprefix("/data/")
            if not (os.path.exists("/data") and os.access("/data", os.W_OK)):
                return (PROJECT_ROOT / "data" / sub).resolve()
        p = Path(self.CHROMA_PERSIST_DIRECTORY)
        if not p.is_absolute() and not posix_val.startswith("/"):
            return (PROJECT_ROOT / p).resolve()
        return p.resolve()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
