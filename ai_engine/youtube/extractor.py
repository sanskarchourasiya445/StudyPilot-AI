"""
ai_engine/youtube/extractor.py

Responsibility: get a transcript for a YouTube video the FAST, FREE way
- by pulling the video's own caption track via `youtube-transcript-api`
- and fetch lightweight video metadata (title) without downloading any
audio or video.

Why try captions first, before audio + Whisper?
Most YouTube videos (especially lectures, which this project targets)
already have either creator-uploaded or auto-generated captions. Reading
those directly is orders of magnitude faster and cheaper than
downloading the full audio track and running local Whisper transcription
- no download, no ffmpeg, no GPU/CPU-heavy inference. Whisper
(`youtube/transcriber.py` + `youtube/audio_processor.py`) exists purely
as a FALLBACK for the minority of videos with captions disabled or
unavailable. `loaders/youtube_loader.py` is the module that decides
when to fall back; this file only ever tries captions.

--------------------------------------------------------------------
v1.1.2: migrated to youtube-transcript-api v1.x's instance-based API
--------------------------------------------------------------------
This file was originally written against `youtube-transcript-api` v0.6.x,
which exposed a classmethod-based API
(`YouTubeTranscriptApi.list_transcripts(video_id)`). That library later
shipped a breaking v1.x rewrite: the API is now instance-based
(`YouTubeTranscriptApi().list(video_id)`), and `.fetch()` now returns a
typed `FetchedTranscript` object (an iterable of `FetchedTranscriptSnippet`
dataclasses with a `.text` attribute) instead of a list of raw dicts.
This file is written against the current v1.x API -
`requirements.txt` pins `youtube-transcript-api>=1.0.0` accordingly so a
future install never silently reverts to the incompatible v0.6.x shape.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    VideoUnavailable,
)

from ai_engine.loaders.base_loader import LoaderError
from ai_engine.utils.helpers import extract_youtube_video_id

logger = logging.getLogger(__name__)

# Preference order for caption languages. English first (this project's
# primary audience), falling back to auto-generated captions in any
# available language rather than failing outright - a lecture with only
# Hindi auto-captions is still far more useful than nothing.
PREFERRED_CAPTION_LANGUAGES = ["en", "en-US", "en-GB"]


class YouTubeExtractionError(LoaderError):
    """Raised when a video ID cannot be parsed from a URL, or when video
    metadata cannot be fetched at all (private/deleted/region-locked
    video). NOT raised when captions are simply unavailable - that case
    returns None from `get_captions_transcript` so the caller can fall
    back to audio transcription instead of treating it as fatal.
    """


@dataclass
class VideoMetadata:
    """Lightweight video metadata, fetched without downloading media."""

    video_id: str
    title: str
    duration_seconds: Optional[int]
    channel: Optional[str]


def get_video_metadata(url: str) -> VideoMetadata:
    """Fetch title/duration/channel for a YouTube URL without
    downloading any audio or video.

    Uses yt-dlp's metadata-only extraction (`download=False`), which is
    still needed even in the captions-only happy path, since captions
    alone don't carry a human-readable title for citations/UI display.

    Raises:
        YouTubeExtractionError: if the video ID can't be parsed, or the
        video is unavailable/private/deleted.
    """
    video_id = extract_youtube_video_id(url)
    if video_id is None:
        raise YouTubeExtractionError(f"Could not parse a video ID from URL: {url}")

    ydl_opts = {"quiet": True, "skip_download": True, "no_warnings": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:  # noqa: BLE001 - yt-dlp raises its own broad
        # DownloadError hierarchy; we normalize to our own exception so
        # callers only need to know about YouTubeExtractionError.
        raise YouTubeExtractionError(f"Failed to fetch metadata for {url}: {exc}") from exc

    return VideoMetadata(
        video_id=video_id,
        title=info.get("title", "Untitled video"),
        duration_seconds=info.get("duration"),
        channel=info.get("channel") or info.get("uploader"),
    )


def get_captions_transcript(video_id: str) -> Optional[str]:
    """Attempt to fetch the video's caption track and return it as a
    single plain-text transcript.

    Returns:
        The joined transcript text, or None if no caption track is
        available in any preferred language (disabled, none exist).
        Returning None (rather than raising) is deliberate: "no
        captions" is an expected, common case that
        `loaders/youtube_loader.py` handles by falling back to audio +
        Whisper, not an error condition.
    """
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
    except VideoUnavailable as exc:
        # A genuinely deleted/private/region-locked video - the Whisper
        # fallback (which also needs to download the video) would fail
        # for the same reason, so this is a hard failure, not a "try
        # something else" case.
        raise YouTubeExtractionError(f"Video {video_id} is unavailable: {exc}") from exc
    except CouldNotRetrieveTranscript as exc:
        # The common base class for every other "couldn't get captions
        # this way" outcome: TranscriptsDisabled, NoTranscriptFound,
        # IpBlocked/RequestBlocked (rate limiting or datacenter IP
        # blocks), YouTubeRequestFailed (transient network/HTML-parsing
        # failure), AgeRestricted, VideoUnplayable, PoTokenRequired,
        # CookieError, etc. All of these mean "this specific approach
        # didn't work" - exactly the signal `loaders/youtube_loader.py`
        # needs to fall back to downloading audio + Whisper, so we
        # return None here rather than letting any of these propagate
        # uncaught.
        logger.info(
            "Could not retrieve captions for video %s (%s) - will fall back if possible.",
            video_id,
            type(exc).__name__,
        )
        return None

    transcript = None
    try:
        transcript = transcript_list.find_transcript(PREFERRED_CAPTION_LANGUAGES)
    except NoTranscriptFound:
        # Fall back to whatever caption track exists (e.g. auto-generated
        # captions in the video's original language) rather than giving
        # up just because English isn't available.
        try:
            transcript = next(iter(transcript_list))
        except StopIteration:
            logger.info(
                "Caption list existed but contained no usable transcript for video %s.",
                video_id,
            )
            return None

    try:
        fetched = transcript.fetch()
    except Exception as exc:  # noqa: BLE001 - network/parsing failures
        # from the underlying API; treat as "no captions available"
        # rather than aborting the whole load.
        logger.warning("Failed to fetch caption segments for %s: %s", video_id, exc)
        return None

    # `fetched` is a `FetchedTranscript` - an iterable of
    # `FetchedTranscriptSnippet` dataclasses (`.text`, `.start`,
    # `.duration`), not the raw list-of-dicts the v0.6.x API returned.
    text = " ".join(snippet.text.strip() for snippet in fetched if snippet.text)
    text = text.strip()
    return text or None