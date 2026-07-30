"""
ai_engine/utils/summary_cache.py

Responsibility: session-safe, memory-backed cache for ingested resource summaries.

Prevents redundant map-reduce LLM operations during repeated summary, notes, or quiz
generation runs on the same ingested resource. Designed behind a clean data-access
interface so future backend phases can persist it to PostgreSQL/Redis without changing
AIEngine method signatures.
"""

from __future__ import annotations

import datetime as _dt
import logging
from dataclasses import dataclass
from typing import Dict, Optional

from ai_engine.config import SUMMARY_CACHE_VERSION, get_summary_config_hash

logger = logging.getLogger(__name__)


@dataclass
class SummaryCacheRecord:
    """One stored summary cache entry."""

    resource_id: str
    source: str
    summary: str
    created_at: str
    version: str
    config_hash: str


class SummaryCache:
    """Session-safe memory store for generated resource summaries."""

    def __init__(self) -> None:
        self._cache: Dict[str, SummaryCacheRecord] = {}

    def get(
        self, resource_id: str, current_config_hash: Optional[str] = None
    ) -> Optional[SummaryCacheRecord]:
        """Fetch a cached summary by `resource_id`.

        Returns None if not found, or if the entry is stale due to a cache
        version / configuration mismatch.
        """
        if not resource_id or resource_id not in self._cache:
            return None

        record = self._cache[resource_id]
        expected_hash = current_config_hash or get_summary_config_hash()

        if record.version != SUMMARY_CACHE_VERSION or record.config_hash != expected_hash:
            logger.info(
                "Cache entry for resource_id '%s' is stale (version/config mismatch). Invalidating.",
                resource_id,
            )
            self.invalidate(resource_id)
            return None

        logger.info("Summary cache HIT for resource_id '%s'.", resource_id)
        return record

    def set(
        self,
        resource_id: str,
        source: str,
        summary: str,
        current_config_hash: Optional[str] = None,
    ) -> SummaryCacheRecord:
        """Store a newly generated summary for a resource."""
        now_iso = _dt.datetime.now(_dt.timezone.utc).isoformat()
        cfg_hash = current_config_hash or get_summary_config_hash()

        record = SummaryCacheRecord(
            resource_id=resource_id,
            source=source,
            summary=summary,
            created_at=now_iso,
            version=SUMMARY_CACHE_VERSION,
            config_hash=cfg_hash,
        )
        self._cache[resource_id] = record
        logger.info("Cached summary for resource_id '%s' (%s).", resource_id, source)
        return record

    def invalidate(self, resource_id: str) -> bool:
        """Explicitly remove a summary from cache (e.g. when deleted)."""
        if resource_id in self._cache:
            del self._cache[resource_id]
            logger.info("Invalidated summary cache for resource_id '%s'.", resource_id)
            return True
        return False

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)
