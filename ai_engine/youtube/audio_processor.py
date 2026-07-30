"""
ai_engine/youtube/audio_processor.py

Responsibility: FALLBACK path for when a YouTube video has no usable
caption track (see `youtube/extractor.py`). Downloads the video's audio,
normalizes it to 16kHz mono WAV (what Whisper expects), and splits it
into fixed-length chunks so `youtube/transcriber.py` can process a
multi-hour lecture without loading the entire audio file into memory at
once.

This module is intentionally the ONLY place in the engine that touches
yt-dlp for downloading (as opposed to `youtube/extractor.py`, which only
uses yt-dlp for lightweight, download-free metadata) and the only place
that touches pydub for audio manipulation.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import yt_dlp
from pydub import AudioSegment

from ai_engine.config import (
    AUDIO_CHANNELS,
    AUDIO_CHUNK_MINUTES,
    AUDIO_DOWNLOAD_DIR,
    AUDIO_SAMPLE_RATE,
)
from ai_engine.loaders.base_loader import LoaderError

logger = logging.getLogger(__name__)


class AudioProcessingError(LoaderError):
    """Raised when audio cannot be downloaded, converted, or chunked."""


def download_audio(url: str, video_id: str) -> Path:
    """Download and extract the audio track of a YouTube video as WAV.

    Args:
        url: the full YouTube URL.
        video_id: the parsed video ID (used to build a deterministic,
        collision-free output filename under AUDIO_DOWNLOAD_DIR).

    Returns:
        Path to the downloaded WAV file.

    Raises:
        AudioProcessingError: on any download or extraction failure.
    """
    AUDIO_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    output_template = str(AUDIO_DOWNLOAD_DIR / f"{video_id}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    try:
        logger.info("Downloading audio for video %s...", video_id)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
    except Exception as exc:  # noqa: BLE001 - normalize yt-dlp's broad
        # DownloadError hierarchy into our own domain exception.
        raise AudioProcessingError(f"Failed to download audio for {url}: {exc}") from exc

    wav_path = AUDIO_DOWNLOAD_DIR / f"{video_id}.wav"
    if not wav_path.is_file():
        raise AudioProcessingError(
            f"Expected downloaded audio at {wav_path} but it was not found "
            f"(FFmpeg post-processing may have failed)."
        )

    logger.info("Downloaded audio to %s", wav_path)
    return wav_path


def normalize_audio(wav_path: Path) -> Path:
    """Convert audio to 16kHz mono WAV, the format Whisper expects.

    Downloaded audio from yt-dlp is often already close to this, but
    normalizing explicitly avoids relying on yt-dlp's default encoding
    settings staying compatible with Whisper's expectations.
    """
    try:
        audio = AudioSegment.from_wav(str(wav_path))
        audio = audio.set_channels(AUDIO_CHANNELS).set_frame_rate(AUDIO_SAMPLE_RATE)
        normalized_path = wav_path.with_name(f"{wav_path.stem}_normalized.wav")
        audio.export(str(normalized_path), format="wav")
    except Exception as exc:  # noqa: BLE001
        raise AudioProcessingError(f"Failed to normalize audio {wav_path}: {exc}") from exc

    return normalized_path


def chunk_audio(wav_path: Path, chunk_minutes: int = AUDIO_CHUNK_MINUTES) -> List[Path]:
    """Split a WAV file into fixed-length chunks.

    Chunking keeps memory bounded during transcription and lets
    `transcriber.py` report incremental progress on long lectures instead
    of blocking on the entire file at once.
    """
    try:
        audio = AudioSegment.from_wav(str(wav_path))
    except Exception as exc:  # noqa: BLE001
        raise AudioProcessingError(f"Failed to read audio for chunking: {exc}") from exc

    chunk_ms = chunk_minutes * 60 * 1000
    chunk_paths: List[Path] = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start : start + chunk_ms]
        chunk_path = wav_path.with_name(f"{wav_path.stem}_chunk_{i}.wav")
        chunk.export(str(chunk_path), format="wav")
        chunk_paths.append(chunk_path)

    if not chunk_paths:
        raise AudioProcessingError(f"Chunking produced zero chunks for {wav_path}.")

    logger.info("Split %s into %d chunk(s).", wav_path.name, len(chunk_paths))
    return chunk_paths


def prepare_audio_chunks(url: str, video_id: str) -> List[Path]:
    """End-to-end convenience wrapper: download -> normalize -> chunk.

    This is the single function `loaders/youtube_loader.py` calls when
    falling back from captions to Whisper transcription - it doesn't
    need to know about the three intermediate steps.
    """
    raw_path = download_audio(url, video_id)
    normalized_path = normalize_audio(raw_path)
    return chunk_audio(normalized_path)