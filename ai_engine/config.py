"""
ai_engine/config.py

Single source of configuration for the AI Engine.

This is a plain Python module of constants, not a validated settings
class. For a project whose values (chunk size, retriever k, which model
to use) get tuned frequently during development, a flat file you can
read top to bottom and edit directly is more useful than a
pydantic-settings layer with its own indirection.

Note: LLM / third-party API keys are NOT stored here. Each provider file
(e.g. ai_engine/llm/gemini.py) loads its own key directly from the
environment via python-dotenv. Keys are secrets and shouldn't sit next
to plain, non-secret settings like chunk size - so they stay local to
the file that actually uses them.

To change any behavior of the AI Engine (chunk size, retriever settings,
which Whisper model to use, etc.), edit the values below. No other file
should hardcode a value that belongs here.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
# PROJECT_ROOT = the ai_engine/ package's parent folder, so paths resolve
# correctly regardless of the current working directory the engine is
# launched from (important once this is imported from a FastAPI app
# living in a sibling directory).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Where raw source documents (PDFs, TXT files) are dropped for ingestion.
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"

# Where downloaded/converted audio (from YouTube or uploaded video/audio
# files) is written before transcription. Kept separate from
# DOCUMENTS_DIR because these are intermediate artifacts, not source
# documents themselves.
AUDIO_DOWNLOAD_DIR = PROJECT_ROOT / "data" / "audio"

# Where the persisted Chroma collection lives on disk.
VECTOR_DB_DIR = PROJECT_ROOT / "data" / "chroma_db"

SUPPORTED_FILE_EXTENSIONS = (".pdf", ".txt")


def ensure_dirs() -> None:
    """Create every directory the engine writes to, if missing yet.

    Called once at startup (see engine.py) so ingestion, audio
    processing, and vector store creation never fail on a missing
    folder.
    """
    for directory in (DOCUMENTS_DIR, AUDIO_DOWNLOAD_DIR, VECTOR_DB_DIR):
        directory.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------
# YouTube / Audio processing
# ---------------------------------------------------------------------
# How many minutes of audio go into each chunk before transcription.
# Chunking long audio keeps memory bounded and lets Whisper process a
# multi-hour video without loading it all at once.
AUDIO_CHUNK_MINUTES = 10

# Target sample rate / channels for normalized WAV audio. 16kHz mono is
# what Whisper expects internally, so converting up front avoids
# redundant resampling inside the transcription step.
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1

# ---------------------------------------------------------------------
# Transcription (local Whisper)
# ---------------------------------------------------------------------
# "tiny" | "base" | "small" | "medium" | "large". Larger models are more
# accurate but slower and heavier on memory - "small" is a reasonable
# default for CPU-only environments.
WHISPER_MODEL = "small"
WHISPER_TASK = "transcribe"

# ---------------------------------------------------------------------
# Preprocessing / Chunking (for text going into the vector store)
# ---------------------------------------------------------------------
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# ---------------------------------------------------------------------
# Embeddings (local, free - no API key needed)
# ---------------------------------------------------------------------
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DEVICE = "cpu"  # "cpu" or "cuda"

# ---------------------------------------------------------------------
# Vector store (Chroma)
# ---------------------------------------------------------------------
CHROMA_COLLECTION_NAME = "ai_engine_collection"

# ---------------------------------------------------------------------
# Retriever (MMR - Maximal Marginal Relevance)
# ---------------------------------------------------------------------
RETRIEVER_TYPE = "mmr"
TOP_K = 4          # how many chunks the retriever returns
FETCH_K = 20       # how many candidates MMR considers before diversifying
LAMBDA_MULT = 0.5  # 1.0 = pure relevance, 0.0 = pure diversity

# ---------------------------------------------------------------------
# LLM (Gemini)
# ---------------------------------------------------------------------
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_DEFAULT_TEMPERATURE = 0.3

# ---------------------------------------------------------------------
# Prompting
# ---------------------------------------------------------------------
NO_ANSWER_MESSAGE = "I could not find this information in the provided content."

# ---------------------------------------------------------------------
# Services (chat / summary / notes / quiz)
# ---------------------------------------------------------------------
# Summarization: size of text pieces fed to the map step of the
# map-reduce summarizer. Larger than the retrieval CHUNK_SIZE above
# because summarization wants broader context per LLM call, not
# retrieval-optimized granularity.
SUMMARY_MAP_CHUNK_SIZE = 20000
SUMMARY_MAP_CHUNK_OVERLAP = 1000
SUMMARY_CACHE_VERSION = "1.0"


def get_summary_config_hash() -> str:
    """Return a deterministic fingerprint string representing the current
    summary chunking, prompt, and model configuration to invalidate stale cache
    entries automatically when configuration changes."""
    import hashlib
    raw = f"{SUMMARY_MAP_CHUNK_SIZE}:{SUMMARY_MAP_CHUNK_OVERLAP}:{SUMMARY_CACHE_VERSION}:{GEMINI_MODEL}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

# Quiz generation defaults.
DEFAULT_QUIZ_QUESTION_COUNT = 5
QUIZ_DIFFICULTY_LEVELS = ("easy", "medium", "hard")

# Notes generation default style.
DEFAULT_NOTES_STYLE = "bullet"  # "bullet" or "cornell"

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# ---------------------------------------------------------------------
# Engine metadata (v1.1 addition)
# ---------------------------------------------------------------------
# Reported by AIEngine.version() and included in AIEngine.health() so a
# consuming backend can log/display which engine build it's running
# against without hardcoding the string itself.
ENGINE_VERSION = "1.1.0"

GEMINI_MAX_RETRIES = 5
GEMINI_RETRY_BASE_DELAY_SECONDS = 3.0
GEMINI_RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)