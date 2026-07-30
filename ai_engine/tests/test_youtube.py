"""
ai_engine/tests/test_youtube.py

Unit tests for the YouTube pipeline (`youtube/extractor.py`,
`loaders/youtube_loader.py`). Mocks `youtube_transcript_api` and
`yt_dlp` so these tests run without network access and verify the
captions-first / Whisper-fallback ORCHESTRATION logic, which is the
actual engine code worth testing - not third-party libraries.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ai_engine.loaders.youtube_loader import YouTubeLoadError, YouTubeLoader
from ai_engine.youtube.extractor import VideoMetadata


def _fake_metadata(video_id: str = "abc123XYZ90") -> VideoMetadata:
    return VideoMetadata(
        video_id=video_id,
        title="Intro to Neural Networks",
        duration_seconds=600,
        channel="Study Channel",
    )


def test_can_handle_accepts_youtube_urls() -> None:
    assert YouTubeLoader.can_handle("https://www.youtube.com/watch?v=abc123XYZ90") is True
    assert YouTubeLoader.can_handle("https://youtu.be/abc123XYZ90") is True


def test_can_handle_rejects_non_youtube_urls() -> None:
    assert YouTubeLoader.can_handle("https://example.com/video") is False
    assert YouTubeLoader.can_handle("/local/path/file.pdf") is False


@patch("ai_engine.loaders.youtube_loader.get_video_metadata")
@patch("ai_engine.loaders.youtube_loader.get_captions_transcript")
def test_load_uses_captions_when_available(
    mock_get_captions: MagicMock, mock_get_metadata: MagicMock
) -> None:
    mock_get_metadata.return_value = _fake_metadata()
    mock_get_captions.return_value = "This lecture covers backpropagation and gradient descent."

    loader = YouTubeLoader("https://www.youtube.com/watch?v=abc123XYZ90")
    documents = loader.load()

    assert len(documents) == 1
    assert documents[0].metadata["transcript_source"] == "captions"
    assert documents[0].metadata["source_type"] == "youtube"
    assert "backpropagation" in documents[0].page_content


@patch("ai_engine.loaders.youtube_loader.transcribe_chunks")
@patch("ai_engine.loaders.youtube_loader.prepare_audio_chunks")
@patch("ai_engine.loaders.youtube_loader.get_video_metadata")
@patch("ai_engine.loaders.youtube_loader.get_captions_transcript")
def test_load_falls_back_to_whisper_when_no_captions(
    mock_get_captions: MagicMock,
    mock_get_metadata: MagicMock,
    mock_prepare_audio: MagicMock,
    mock_transcribe: MagicMock,
) -> None:
    mock_get_metadata.return_value = _fake_metadata()
    mock_get_captions.return_value = None  # no captions available
    mock_prepare_audio.return_value = ["/tmp/chunk_0.wav", "/tmp/chunk_1.wav"]
    mock_transcribe.return_value = "Transcribed via Whisper fallback."

    loader = YouTubeLoader("https://www.youtube.com/watch?v=abc123XYZ90")
    documents = loader.load()

    assert documents[0].metadata["transcript_source"] == "whisper"
    assert documents[0].page_content == "Transcribed via Whisper fallback."
    mock_prepare_audio.assert_called_once()
    mock_transcribe.assert_called_once()


@patch("ai_engine.loaders.youtube_loader.prepare_audio_chunks")
@patch("ai_engine.loaders.youtube_loader.get_video_metadata")
@patch("ai_engine.loaders.youtube_loader.get_captions_transcript")
def test_load_raises_when_both_strategies_fail(
    mock_get_captions: MagicMock,
    mock_get_metadata: MagicMock,
    mock_prepare_audio: MagicMock,
) -> None:
    from ai_engine.loaders.base_loader import LoaderError

    mock_get_metadata.return_value = _fake_metadata()
    mock_get_captions.return_value = None
    mock_prepare_audio.side_effect = LoaderError("download failed: video is private")

    loader = YouTubeLoader("https://www.youtube.com/watch?v=abc123XYZ90")
    with pytest.raises(YouTubeLoadError):
        loader.load()