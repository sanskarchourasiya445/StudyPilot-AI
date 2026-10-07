"""
ai_engine/loaders/youtube_loader.py

Responsibility: turn a YouTube URL into a `Document`. This is the
ORCHESTRATOR for the two-tier transcription strategy:

  1. Try captions first (`youtube.extractor.get_captions_transcript`) -
     fast, free, no download.
  2. If no captions exist, fall back to downloading audio
     (`youtube.audio_processor.prepare_audio_chunks`) and running local
     Whisper transcription (`youtube.transcriber.transcribe_chunks`).

Everything downstream of this loader (chunking, embeddings, vector
store, services) receives a plain `Document` and has no idea whether the
transcript came from captions or Whisper - that distinction is recorded
in metadata (`transcript_source`) purely for transparency/debugging, not
because any other layer branches on it.
"""

from __future__ import annotations

import logging
from typing import List

from langchain_core.documents import Document

from ai_engine.loaders.base_loader import BaseLoader, LoaderError
from ai_engine.utils.helpers import is_youtube_url
from ai_engine.youtube.audio_processor import prepare_audio_chunks
from ai_engine.youtube.extractor import (
    YouTubeExtractionError,
    get_captions_transcript,
    get_video_metadata,
)
from ai_engine.youtube.transcriber import transcribe_chunks
from ai_engine.utils.exceptions import YouTubeLoadError

logger = logging.getLogger(__name__)


class YouTubeLoader(BaseLoader):
    """Loads a YouTube URL into a single transcript `Document`.

    Metadata set on the returned Document:
      - source_type: always "youtube"
      - source: the video title (human-readable, used for citations)
      - video_id, channel, duration_seconds: from `VideoMetadata`
      - transcript_source: "captions" or "whisper", whichever succeeded
      - ingested_at: not set here directly; added uniformly by
        `preprocessing/metadata.py` for all source types, so ingestion
        timestamps stay consistent across loaders.
    """

    @classmethod
    def can_handle(cls, source: str) -> bool:
        """True if `source` is a recognizable YouTube URL."""
        return is_youtube_url(source)

    def load(self) -> List[Document]:
        """Fetch metadata, then attempt captions, then fall back to
        audio + Whisper if captions are unavailable.

        Raises:
            YouTubeLoadError: if metadata can't be fetched, or if BOTH
            the captions and Whisper-fallback strategies fail.
        """
        try:
            metadata = get_video_metadata(self.source)
        except YouTubeExtractionError as exc:
            raise YouTubeLoadError(str(exc)) from exc

        logger.info("Processing YouTube video: %s (%s)", metadata.title, metadata.video_id)

        transcript_text = None
        transcript_source = None

        try:
            transcript_text = get_captions_transcript(metadata.video_id)
        except YouTubeExtractionError as exc:
            # A hard failure while fetching captions (e.g. video became
            # unavailable between metadata fetch and this call) is
            # logged but not fatal yet - we still try the Whisper
            # fallback before giving up entirely.
            logger.warning("Caption fetch failed for %s: %s", metadata.video_id, exc)

        if transcript_text:
            transcript_source = "captions"
            logger.info("Using caption track for %s.", metadata.video_id)
        else:
            logger.info(
                "No captions available for %s - falling back to audio + Whisper.",
                metadata.video_id,
            )
            try:
                chunk_paths = prepare_audio_chunks(self.source, metadata.video_id)
                transcript_text = transcribe_chunks(chunk_paths)
                transcript_source = "whisper"
            except LoaderError as exc:
                raise YouTubeLoadError(
                    f"Both caption extraction and Whisper fallback failed for "
                    f"'{metadata.title}' ({metadata.video_id}): {exc}"
                ) from exc

        document = Document(
            page_content=transcript_text,
            metadata={
                "source_type": "youtube",
                "source": metadata.title,
                "video_id": metadata.video_id,
                "channel": metadata.channel,
                "duration_seconds": metadata.duration_seconds,
                "transcript_source": transcript_source,
            },
        )

        logger.info(
            "Loaded YouTube transcript for '%s' via %s (%d characters).",
            metadata.title,
            transcript_source,
            len(transcript_text),
        )
        return [document]