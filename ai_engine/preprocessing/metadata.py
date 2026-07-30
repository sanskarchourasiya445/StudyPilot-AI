"""
ai_engine/preprocessing/metadata.py

Responsibility: apply the final, uniform metadata pass to chunks right
before they're embedded and stored - the last stage of the shared
pipeline before source-specific concerns disappear entirely.

Why a separate stage from chunking/cleaning instead of folding this into
the chunker?
Chunking is about WHERE to split text; this stage is about WHAT every
chunk must carry to be usable later (a stable ID for
citation/deduplication, a normalized ingestion timestamp, and a
guarantee that required keys exist even if a loader forgot one). Keeping
this separate means a future change to "what metadata every chunk needs"
touches one file, not the splitting logic itself.

--------------------------------------------------------------------
v1.1 addition: resource-level identity
--------------------------------------------------------------------
Every chunk now also carries a `resource_id` - a single ID shared by
every chunk that came from the same `AIEngine.ingest()` call. This is
what a consuming backend uses as the join key between its own
`Resource` row (in Postgres) and this engine's vector store: "delete
resource X" now means "delete every chunk whose resource_id == X"
(see `vectorstore/chroma.py::delete_by_resource_id`), regardless of
what the resource happened to be named - fixing a real bug in the
pre-v1.1 design, where two different resources sharing the same
`source` string (e.g. two students both uploading a file called
"notes.pdf", or two YouTube videos with the same title) would have
had their chunk_index sequences and per-source lookups collide.
`chunk_index` is therefore now counted per `resource_id`, not per
`source`, below - this only changes an internal counting key, no
existing metadata key is removed or renamed.

New keys added to every chunk's metadata (all additive - no existing
key is removed, renamed, or overwritten if already present):
  - resource_id: unique per ingested resource (see above).
  - workspace_id: optional, caller-supplied; always present as a key
    (None if not supplied) so that Chroma `where` filters on it never
    have to special-case a missing key.
  - user_id: optional, caller-supplied; same reasoning as workspace_id.
  - resource_type: mirrors `source_type` under the name this project's
    backend spec expects. `source_type` is kept untouched for any
    existing code that reads it.
  - uploaded_at: mirrors `ingested_at` under the name the backend spec
    expects. `ingested_at` is kept untouched for the same reason.
  - page: defaulted to None where a loader doesn't set one (TXT,
    YouTube), so every chunk has the key regardless of source type.
"""

from __future__ import annotations

import datetime as _dt
import logging
from typing import List, Optional

from langchain_core.documents import Document

from ai_engine.utils.helpers import new_chunk_id, new_resource_id

logger = logging.getLogger(__name__)

# Every chunk stored in the vector store must have these keys so that
# citations, source-filtering (services/chat_service.py), and
# per-source retrieval (vectorstore/chroma.py's `get_documents_by_source`)
# never have to special-case a missing key.
_REQUIRED_KEYS_WITH_DEFAULTS = {
    "source": "unknown",
    "source_type": "unknown",
}


def enrich_chunk_metadata(
    chunks: List[Document],
    resource_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
) -> List[Document]:
    """Attach a stable chunk_id, a normalized ingestion timestamp, a
    per-resource sequential chunk_index, and (v1.1) resource-level
    identity metadata to every chunk. Fills in any missing required
    keys with a safe default rather than raising, since a missing key
    here should degrade citation quality, not abort ingestion of
    otherwise-good content.

    Args:
        chunks: the chunks to enrich (mutated in place).
        resource_id: shared identifier for every chunk in this batch -
            i.e. every chunk that came from the same ingested resource.
            If not given (e.g. a caller invoking this function directly
            rather than through `AIEngine.ingest()`), one is generated
            automatically so the function never produces chunks lacking
            a `resource_id` - existing callers that don't pass this
            argument keep working exactly as before, just with an
            auto-generated ID added.
        workspace_id: optional caller-supplied workspace scope.
        user_id: optional caller-supplied owner scope.
        resource_type: optional override for the `resource_type` key. If
            not given, each chunk's own `source_type` is mirrored into
            `resource_type` individually.

    Mutates and returns the same list (each chunk's `.metadata` dict is
    updated in place) - avoids doubling memory for large ingestion
    batches, consistent with `cleaner.clean_documents`.
    """
    if not chunks:
        logger.warning("enrich_chunk_metadata called with an empty chunk list.")
        return chunks

    resolved_resource_id = resource_id or new_resource_id()
    ingested_at = _dt.datetime.now(_dt.timezone.utc).isoformat()
    per_resource_counter: dict = {}

    for chunk in chunks:
        for key, default in _REQUIRED_KEYS_WITH_DEFAULTS.items():
            if key not in chunk.metadata or chunk.metadata[key] in (None, ""):
                logger.debug(
                    "Chunk missing metadata key '%s' - defaulting to %r.", key, default
                )
                chunk.metadata[key] = default

        # chunk_index is now counted per resource_id (not per `source`,
        # as in v1.0) - see the module docstring for why this is a
        # correctness fix bundled with introducing resource_id, not a
        # breaking change to any existing consumer.
        chunk_index = per_resource_counter.get(resolved_resource_id, 0)

        chunk.metadata["chunk_id"] = new_chunk_id()
        chunk.metadata["chunk_index"] = chunk_index
        # Only set ingested_at if the loader didn't already stamp one -
        # PDF/TXT loaders set it per-document at load time; we don't
        # want to overwrite that with a slightly later "now" just
        # because chunking happened a moment afterward.
        chunk.metadata.setdefault("ingested_at", ingested_at)

        # ---------------- v1.1 additive metadata ----------------
        chunk.metadata["resource_id"] = resolved_resource_id
        chunk.metadata["workspace_id"] = workspace_id
        chunk.metadata["user_id"] = user_id
        chunk.metadata["resource_type"] = resource_type or chunk.metadata.get(
            "source_type", "unknown"
        )
        chunk.metadata.setdefault("uploaded_at", chunk.metadata["ingested_at"])
        chunk.metadata.setdefault("page", None)

        per_resource_counter[resolved_resource_id] = chunk_index + 1

    logger.info(
        "Enriched metadata for %d chunk(s) under resource_id=%s.",
        len(chunks),
        resolved_resource_id,
    )
    return chunks