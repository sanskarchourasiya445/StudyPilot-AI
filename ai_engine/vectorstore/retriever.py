"""
ai_engine/vectorstore/retriever.py

Responsibility: turn a Chroma vector store into a configured retriever.
This is where retrieval STRATEGY lives, isolated from both the vector
store (storage concern, chroma.py) and the pipeline/services
(orchestration concern).

Why MMR (Maximal Marginal Relevance) instead of plain similarity search?
Plain top-K similarity can return several near-duplicate chunks (e.g.
the same definition repeated in a lecture transcript and an
accompanying slide-deck PDF), wasting context budget on redundant
evidence. MMR first fetches a larger candidate pool (fetch_k) by
similarity, then greedily selects `top_k` of them while penalizing
chunks too similar to ones already selected - so the final set is both
relevant AND diverse.

Why support an optional `source_filter`?
StudyPilot is a multi-document workspace - a student may have uploaded
five PDFs and two lecture videos. Sometimes they want to "chat with
everything", but often they want to ask a question scoped to ONE
uploaded item ("what does chapter 3 of THIS pdf say"). Rather than
retrieving broadly and hoping the right document wins on relevance
alone, we let the caller (`services/chat_service.py`, driven by
`AIEngine.chat(source_filter=...)`) constrain retrieval to a specific
`source` via Chroma's native metadata filtering.

--------------------------------------------------------------------
v1.1 addition: resource_id / workspace_id / user_id filters
--------------------------------------------------------------------
`source_filter` alone has the collision problem described in
`preprocessing/metadata.py`'s v1.1 docstring (two resources can share a
`source` string). `resource_id`, `workspace_id`, and `user_id` filters
are added as additional, independently-optional scopes, composed via
`vectorstore.chroma.build_metadata_filter`. Passing only `source_filter`
(as every v1.0 caller does) produces the exact same single-key filter
dict as before - this is purely additive.
"""

from __future__ import annotations

import logging
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStoreRetriever

from ai_engine.config import FETCH_K, LAMBDA_MULT, TOP_K
from ai_engine.vectorstore.chroma import build_metadata_filter

logger = logging.getLogger(__name__)


class RetrieverConfigError(Exception):
    """Raised when retriever configuration is invalid (e.g. fetch_k
    smaller than top_k, which would give MMR nothing to diversify over)."""


def build_retriever(
    vector_store: Chroma,
    top_k: int = TOP_K,
    fetch_k: int = FETCH_K,
    lambda_mult: float = LAMBDA_MULT,
    source_filter: Optional[str] = None,
    resource_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> VectorStoreRetriever:
    """Build an MMR-configured retriever from an existing vector store.

    Args:
        vector_store: an already-open Chroma store (see `chroma.py`).
        top_k: number of chunks to return.
        fetch_k: candidate pool size MMR selects from before
        diversifying. Must be >= top_k.
        lambda_mult: 1.0 = pure relevance, 0.0 = pure diversity.
        source_filter: if given, restrict retrieval to chunks whose
        `source` metadata exactly matches this value (see module
        docstring).
        resource_id: (v1.1) if given, restrict retrieval to one
        specific ingested resource - preferred over `source_filter`
        where available, since it cannot collide across resources that
        happen to share a name.
        workspace_id: (v1.1) if given, restrict retrieval to one
        workspace.
        user_id: (v1.1) if given, restrict retrieval to one user's
        resources.
        If none of the filter arguments are given, retrieval spans the
        entire workspace, exactly as in v1.0.

    Raises:
        RetrieverConfigError: if fetch_k < top_k.
    """
    if fetch_k < top_k:
        raise RetrieverConfigError(
            f"fetch_k ({fetch_k}) must be >= top_k ({top_k}) for MMR to have "
            f"a meaningful candidate pool to diversify over."
        )

    search_kwargs = {"k": top_k, "fetch_k": fetch_k, "lambda_mult": lambda_mult}
    metadata_filter = build_metadata_filter(
        source=source_filter,
        resource_id=resource_id,
        workspace_id=workspace_id,
        user_id=user_id,
    )
    if metadata_filter is not None:
        search_kwargs["filter"] = metadata_filter

    logger.info(
        "Building MMR retriever (top_k=%d, fetch_k=%d, lambda_mult=%.2f, filter=%s)",
        top_k,
        fetch_k,
        lambda_mult,
        metadata_filter or "<all sources>",
    )

    return vector_store.as_retriever(search_type="mmr", search_kwargs=search_kwargs)