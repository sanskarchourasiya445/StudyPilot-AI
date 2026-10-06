from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Storage Paths & Limits
    CHROMA_PERSIST_DIRECTORY: str = "data/chroma_db"
    UPLOAD_DIR: str = "data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    FRONTEND_DIST_DIR: str = "frontend/dist"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
