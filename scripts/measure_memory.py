"""
scripts/measure_memory.py

Memory & Performance measurement tool for StudyPilot AI.
Measures process RSS (in MB) at each step of the pipeline.
"""
from __future__ import annotations

import gc
import os
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import psutil

process = psutil.Process(os.getpid())


def get_rss_mb() -> float:
    """Return current process RSS in MB."""
    return process.memory_info().rss / (1024 * 1024)


def main():
    print("=" * 60)
    print("STUDYPILOT AI - PRODUCTION MEMORY & PERFORMANCE PROFILE")
    print("=" * 60)

    # 1. Baseline Startup RSS
    rss_startup = get_rss_mb()
    print(f"MEMORY: startup = {rss_startup:.2f} MB")

    # 2. Import Backend Modules (without initializing AIEngine)
    t0 = time.perf_counter()
    from backend.app.core.config import settings
    from backend.app.main import app
    rss_after_backend_import = get_rss_mb()
    print(f"MEMORY: after_backend_import = {rss_after_backend_import:.2f} MB (delta: +{rss_after_backend_import - rss_startup:.2f} MB)")

    # 3. Before AIEngine initialization
    from backend.app.ai.engine_provider import get_ai_engine
    rss_before_ai = get_rss_mb()
    print(f"MEMORY: before_ai_engine = {rss_before_ai:.2f} MB")

    # 4. Initialize AIEngine (loads MiniLM + Chroma)
    t_ai_0 = time.perf_counter()
    engine = get_ai_engine()
    t_ai_1 = time.perf_counter()
    rss_after_ai = get_rss_mb()
    print(f"MEMORY: after_ai_engine = {rss_after_ai:.2f} MB (delta: +{rss_after_ai - rss_before_ai:.2f} MB, time: {t_ai_1 - t_ai_0:.2f}s)")

    # 5. Measure PDF Ingestion Pipeline
    # Find a test PDF or the uploaded DSA notes
    test_pdf = None
    candidate_paths = [
        PROJECT_ROOT / "data" / "uploads" / "00d4c333-6f45-4cee-8f15-6a3b2b789c9c" / "DSA_College_Exam_Notes_30_Pages.pdf",
        PROJECT_ROOT / "backend" / "tests" / "fixtures" / "sample.pdf",
    ]
    for p in candidate_paths:
        if p.exists():
            test_pdf = p
            break

    if not test_pdf:
        # Search anywhere in data/uploads
        pdfs = list((PROJECT_ROOT / "data" / "uploads").glob("**/*.pdf"))
        if pdfs:
            test_pdf = pdfs[0]

    if test_pdf and test_pdf.exists():
        print(f"\n--- Profiling PDF Ingestion: {test_pdf.name} ---")
        rss_before_pdf = get_rss_mb()
        print(f"MEMORY: before_pdf_ingest = {rss_before_pdf:.2f} MB")

        # Step A: Load source
        t_load_0 = time.perf_counter()
        from ai_engine.loaders.loader_factory import load_source
        raw_docs = load_source(str(test_pdf))
        t_load_1 = time.perf_counter()
        rss_after_extract = get_rss_mb()
        print(f"MEMORY: pdf_extract = {rss_after_extract:.2f} MB (delta: +{rss_after_extract - rss_before_pdf:.2f} MB, pages: {len(raw_docs)}, time: {t_load_1 - t_load_0:.2f}s)")

        # Step B: Clean & Chunk
        t_chunk_0 = time.perf_counter()
        from ai_engine.preprocessing.cleaner import clean_documents
        from ai_engine.preprocessing.chunker import chunk_documents
        from ai_engine.preprocessing.metadata import enrich_chunk_metadata
        from ai_engine.utils.helpers import new_resource_id

        cleaned = clean_documents(raw_docs)
        chunks = chunk_documents(cleaned)
        enriched = enrich_chunk_metadata(chunks, resource_id=new_resource_id(), user_id="bench_user")
        t_chunk_1 = time.perf_counter()
        rss_after_chunking = get_rss_mb()
        print(f"MEMORY: chunking = {rss_after_chunking:.2f} MB (delta: +{rss_after_chunking - rss_after_extract:.2f} MB, chunks: {len(enriched)}, time: {t_chunk_1 - t_chunk_0:.2f}s)")

        # Step C: Embed & Persist to Chroma
        t_embed_0 = time.perf_counter()
        from ai_engine.vectorstore.chroma import add_documents
        ids = add_documents(engine._vector_store, enriched)
        t_embed_1 = time.perf_counter()
        rss_after_persist = get_rss_mb()
        print(f"MEMORY: after_chroma_persist = {rss_after_persist:.2f} MB (delta: +{rss_after_persist - rss_after_chunking:.2f} MB, vectors_added: {len(ids)}, time: {t_embed_1 - t_embed_0:.2f}s)")

        # Step D: Cleanup & GC
        del raw_docs, cleaned, chunks, enriched, ids
        gc.collect()
        rss_after_gc = get_rss_mb()
        print(f"MEMORY: after_gc = {rss_after_gc:.2f} MB (delta: {rss_after_gc - rss_after_persist:.2f} MB)")

    # 6. Measure Chat Retrieval Query
    print("\n--- Profiling Chat / Retrieval ---")
    rss_before_chat = get_rss_mb()
    t_chat_0 = time.perf_counter()
    chat_res = engine.chat("What is the time complexity of binary search?", user_id="bench_user")
    t_chat_1 = time.perf_counter()
    rss_after_chat = get_rss_mb()
    print(f"MEMORY: after_chat = {rss_after_chat:.2f} MB (delta: +{rss_after_chat - rss_before_chat:.2f} MB, time: {t_chat_1 - t_chat_0:.2f}s)")

    print("\n" + "=" * 60)
    print("FINAL SUMMARY:")
    print(f"Initial Startup:  {rss_startup:.2f} MB")
    print(f"Peak RAM:         {get_rss_mb():.2f} MB")
    print(f"Render Free Limit: 512.00 MB")
    pct = (get_rss_mb() / 512.0) * 100
    print(f"RAM Utilization:   {pct:.1f}% of Render Free 512MB limit")
    print("=" * 60)


if __name__ == "__main__":
    main()
