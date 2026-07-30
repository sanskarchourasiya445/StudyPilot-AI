"""
ai_engine/utils/helpers.py

Small, stateless, cross-cutting helpers used by more than one module.
Rule for what belongs here: no domain ownership (no loading/chunking/LLM
logic), and used in 2+ otherwise-unrelated places. Everything else
belongs in the module that owns that responsibility - this file must not
become a dumping ground for pipeline logic.
"""

from __future__ import annotations

import re
import uuid
from typing import List, Optional
from urllib.parse import parse_qs, urlparse

from langchain_core.documents import Document

# Hostnames that identify a URL as a YouTube video link. Used by
# `loaders/youtube_loader.py` (via `is_youtube_url` /
# `extract_youtube_video_id`) to decide whether a given source string
# should be routed to the YouTube loader.
_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "www.youtu.be",
}


def is_youtube_url(source: str) -> bool:
    """Return True if `source` looks like a YouTube video URL.

    Deliberately a pure string check (no network call) so it's safe and
    cheap to call from `can_handle()` on the loader factory's hot path.
    """
    try:
        parsed = urlparse(source)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and parsed.netloc.lower() in _YOUTUBE_HOSTS


def extract_youtube_video_id(url: str) -> Optional[str]:
    """Extract the 11-character video ID from a YouTube URL.

    Supports both the long form (`youtube.com/watch?v=<id>`) and the
    short form (`youtu.be/<id>`). Returns None if no ID can be found,
    so callers can raise a clear, domain-specific error rather than
    getting a confusing downstream failure.
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.lstrip("/")
        return video_id or None

    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        query = parse_qs(parsed.query)
        video_ids = query.get("v")
        if video_ids:
            return video_ids[0]

    return None


def is_valid_file_path_extension(path: str, allowed_extensions: tuple) -> bool:
    """Case-insensitive suffix check, used by file-based loaders'
    `can_handle()` implementations."""
    return path.lower().endswith(tuple(ext.lower() for ext in allowed_extensions))


def clean_whitespace(text: str) -> str:
    """Collapse repeated whitespace/newlines into single spaces/newlines.

    Shared by both `preprocessing/cleaner.py` (for full-document
    cleaning) and the console-facing summary/notes formatting in the
    services layer, so both use one definition of "clean" rather than
    two subtly different regexes drifting apart over time.
    """
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def new_chunk_id() -> str:
    """Generate a short, unique, human-shareable chunk identifier.

    Used by `preprocessing/metadata.py` to give every chunk a stable ID
    independent of its position in a list (positions shift as documents
    are added/removed from the vector store over time; a UUID does not).
    """
    return uuid.uuid4().hex[:12]


def new_resource_id() -> str:
    """Generate a unique resource identifier (v1.1 addition).

    Unlike `new_chunk_id` (a short id scoped to one chunk), a
    `resource_id` identifies one whole ingested resource (one PDF, one
    YouTube video, one TXT file) and is the join key a consuming backend
    would use as a foreign key against its own `Resource` table - so
    this returns a full, low-collision-probability UUID4 string rather
    than a shortened one.
    """
    return str(uuid.uuid4())


def pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
    """Tiny helper for human-readable messages like '1 file' vs '3 files'."""
    plural = plural or f"{singular}s"
    return f"{count} {singular if count == 1 else plural}"


def format_sources(documents: List[Document], max_preview_chars: int = 100) -> str:
    """Render retrieved chunks as a human-readable, source-attributed
    summary. Used by `services/chat_service.py` to let a caller (console,
    or later a FastAPI response) show which chunks grounded an answer.
    """
    if not documents:
        return "(no sources retrieved)"

    lines = []
    for i, doc in enumerate(documents, start=1):
        source = doc.metadata.get("source", "unknown")
        source_type = doc.metadata.get("source_type", "unknown")
        preview = doc.page_content[:max_preview_chars].replace("\n", " ").strip()
        lines.append(f"[{i}] ({source_type}) {source} — \"{preview}...\"")
    return "\n".join(lines)


def strip_code_fences(text: str) -> str:
    """Remove Markdown code fences (```json ... ``` or ``` ... ```) that
    LLMs frequently wrap structured output in, even when explicitly
    instructed to return raw JSON.

    Used by `services/quiz_service.py` before attempting to parse the
    LLM's response as JSON, so a stray ```` ```json ```` prefix doesn't
    turn a perfectly good response into a parse failure.
    """
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()