"""
ai_engine/utils/logger.py

Responsibility: ONE place that configures how logging looks and behaves
for the whole engine. Every other module still does the standard
`logger = logging.getLogger(__name__)` at module level (so log lines are
correctly attributed to the module that emitted them) - this file does
not replace that pattern, it just gives `AIEngine` (see engine.py) a
single `configure_logging()` call to run once at startup, instead of
scattering `logging.basicConfig(...)` calls (or worse, forgetting to
configure logging at all) across the codebase.

Why a function instead of running `logging.basicConfig()` at import
time?
Configuring logging as an import side effect is surprising and hard to
control from the outside - a consumer embedding this engine in a FastAPI
app (which likely has its own logging configuration) should be able to
import any `ai_engine` module without silently having their root logger
reconfigured. Making it an explicit function that `engine.py` calls once
keeps that decision in the caller's hands.
"""

from __future__ import annotations

import logging

from ai_engine.config import LOG_FORMAT, LOG_LEVEL

_configured = False


def configure_logging(level: str = LOG_LEVEL, fmt: str = LOG_FORMAT) -> None:
    """Configure the root logger for the AI Engine, once.

    Safe to call multiple times - only the first call actually applies
    configuration; subsequent calls are no-ops. This makes it safe for
    both `engine.py` and individual test files to call it defensively
    without worrying about duplicate handlers being attached.

    Args:
        level: standard logging level name (e.g. "INFO", "DEBUG").
        fmt: log line format string.
    """
    global _configured
    if _configured:
        return

    resolved_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=resolved_level, format=fmt)
    _configured = True

    logger = logging.getLogger(__name__)
    logger.debug("Logging configured at level %s", level.upper())


def get_logger(name: str) -> logging.Logger:
    """Thin convenience wrapper around `logging.getLogger`.

    Purely for readability at call sites (`get_logger(__name__)` reads
    slightly clearer than `logging.getLogger(__name__)` when this module
    is already being imported for `configure_logging`), and gives us a
    single seam to later add engine-wide logger customization (e.g.
    attaching a request-id filter once this is embedded in FastAPI)
    without touching every call site.
    """
    return logging.getLogger(name)