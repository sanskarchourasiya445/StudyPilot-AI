"""
ai_engine/youtube/transcriber.py

Responsibility: transcribe audio chunks to text using a local Whisper
model. This is the FALLBACK transcription path, used only when
`youtube/extractor.py` couldn't find a usable caption track and
`youtube/audio_processor.py` has produced downloaded/chunked audio.

Why a lazily-loaded, module-level singleton for the Whisper model?
Loading a Whisper model reads weights from disk (or downloads them on
first use) and allocates real memory - this should happen at most once
per process, not once per audio chunk. A module-level `_model` variable
with a guarded loader function gives us that without needing a class
just to hold one cached value.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

import whisper

from ai_engine.config import WHISPER_MODEL, WHISPER_TASK
from ai_engine.loaders.base_loader import LoaderError

logger = logging.getLogger(__name__)

_model: Optional["whisper.Whisper"] = None


class TranscriptionError(LoaderError):
    """Raised when the Whisper model fails to load, or fails to
    transcribe a given audio chunk."""


def _load_model() -> "whisper.Whisper":
    """Load (or return the already-loaded) Whisper model.

    Raises:
        TranscriptionError: if the model fails to load (missing model
        files, out-of-memory, unsupported model name).
    """
    global _model
    if _model is None:
        try:
            logger.info("Loading Whisper model '%s'...", WHISPER_MODEL)
            _model = whisper.load_model(WHISPER_MODEL)
            logger.info("Whisper model '%s' loaded.", WHISPER_MODEL)
        except Exception as exc:  # noqa: BLE001
            raise TranscriptionError(
                f"Failed to load Whisper model '{WHISPER_MODEL}': {exc}"
            ) from exc
    return _model


def transcribe_chunk(chunk_path: Path) -> str:
    """Transcribe a single audio chunk to text.

    Raises:
        TranscriptionError: if transcription fails for this chunk.
    """
    model = _load_model()
    try:
        result = model.transcribe(str(chunk_path), task=WHISPER_TASK)
    except Exception as exc:  # noqa: BLE001 - normalize any Whisper /
        # torch runtime failure into our own domain exception.
        raise TranscriptionError(f"Failed to transcribe {chunk_path.name}: {exc}") from exc

    return result.get("text", "").strip()


def transcribe_chunks(chunk_paths: List[Path]) -> str:
    """Transcribe a sequence of audio chunks and join them into one
    full transcript, in order.

    Chunks are transcribed sequentially (not in parallel) because the
    underlying Whisper model instance is not guaranteed thread-safe for
    concurrent `.transcribe()` calls, and this project targets CPU
    inference where parallelism would contend for the same cores anyway.
    """
    full_text_parts: List[str] = []

    for i, chunk_path in enumerate(chunk_paths, start=1):
        logger.info("Transcribing chunk %d/%d (%s)...", i, len(chunk_paths), chunk_path.name)
        text = transcribe_chunk(chunk_path)
        full_text_parts.append(text)

    full_transcript = " ".join(part for part in full_text_parts if part).strip()

    if not full_transcript:
        raise TranscriptionError(
            "Whisper produced an empty transcript across all audio chunks."
        )

    logger.info("Transcription complete (%d characters).", len(full_transcript))
    return full_transcript