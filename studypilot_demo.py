"""
StudyPilot AI Engine - Interactive Terminal Demo

A clean, faculty-ready CLI interface for demonstrating StudyPilot AI Engine's
core capabilities (Ingestion, Multi-resource Retrieval, Chat, Summarization,
Notes, and Quiz generation).
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional

from ai_engine.engine import AIEngine, EngineError
from ai_engine.vectorstore.chroma import ResourceRecord


def print_banner() -> None:
    print("=" * 60)
    print("           STUDYPILOT AI ENGINE DEMO           ")
    print("=" * 60)


def print_menu() -> None:
    print("\n---------------- MENU OPTIONS ----------------")
    print("1. Add PDF")
    print("2. Add YouTube URL")
    print("3. List resources")
    print("4. Chat with a selected resource")
    print("5. Generate summary")
    print("6. Generate notes")
    print("7. Generate quiz")
    print("8. Exit")
    print("----------------------------------------------")


def display_resources(resources: List[ResourceRecord]) -> None:
    if not resources:
        print("\n[INFO] No resources ingested yet.")
        return

    print(f"\n[INFO] Ingested Resources ({len(resources)} total):")
    print("-" * 65)
    print(f"{'#':<3} | {'Type':<8} | {'Chunks':<6} | {'Resource ID':<36} | {'Source Name'}")
    print("-" * 65)
    for idx, rec in enumerate(resources, 1):
        r_type = rec.resource_type or "unknown"
        print(f"{idx:<3} | {r_type:<8} | {rec.chunk_count:<6} | {rec.resource_id:<36} | {rec.source}")
    print("-" * 65)


def select_resource(engine: AIEngine, allow_all: bool = False) -> Optional[ResourceRecord]:
    """Helper to fetch resources and prompt user for selection."""
    try:
        resources = engine.list_resources()
    except EngineError as exc:
        print(f"[ERROR] Failed to fetch resources: {exc}")
        return None

    if not resources:
        print("\n[WARN] No resources available. Please ingest a PDF or YouTube video first.")
        return None

    display_resources(resources)

    if allow_all:
        print("0. All Resources (Search across whole workspace)")

    while True:
        prompt_text = "Select a resource number (or 0 for All): " if allow_all else "Select a resource number: "
        choice = input(prompt_text).strip()
        if not choice:
            continue
        if choice == "0" and allow_all:
            return None  # None signifies all resources
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(resources):
                return resources[idx - 1]
        print(f"[ERROR] Invalid selection. Enter a number between {'0' if allow_all else '1'} and {len(resources)}.")


def handle_add_pdf(engine: AIEngine) -> None:
    print("\n--- Add PDF Document ---")
    pdf_path = input("Enter path to PDF file: ").strip().strip('"').strip("'")
    if not pdf_path:
        print("[WARN] No path provided.")
        return

    if not os.path.exists(pdf_path):
        print(f"[ERROR] File does not exist at path: '{pdf_path}'")
        return

    print(f"[...] Ingesting PDF '{pdf_path}'...")
    try:
        result = engine.ingest(pdf_path)
        print(f"\n[OK] PDF Ingested Successfully!")
        print(f"   Resource ID : {result.resource_id}")
        print(f"   Source Name : {result.source}")
        print(f"   Source Type : {result.source_type}")
        print(f"   Pages       : {result.pages_or_segments}")
        print(f"   Chunks      : {result.chunks_created}")

        # Display updated resources
        display_resources(engine.list_resources())
    except EngineError as exc:
        print(f"[ERROR] Ingestion failed: {exc}")


def handle_add_youtube(engine: AIEngine) -> None:
    print("\n--- Add YouTube Video ---")
    yt_url = input("Enter YouTube Video URL: ").strip()
    if not yt_url:
        print("[WARN] No URL provided.")
        return

    print(f"[...] Ingesting YouTube video from '{yt_url}'...")
    try:
        result = engine.ingest(yt_url)
        print(f"\n[OK] YouTube Video Ingested Successfully!")
        print(f"   Resource ID : {result.resource_id}")
        print(f"   Source Name : {result.source}")
        print(f"   Source Type : {result.source_type}")
        print(f"   Chunks      : {result.chunks_created}")

        # Display updated resources
        display_resources(engine.list_resources())
    except EngineError as exc:
        print(f"[ERROR] Ingestion failed: {exc}")


def handle_chat(engine: AIEngine) -> None:
    print("\n--- Chat with AI Engine ---")
    selected_rec = select_resource(engine, allow_all=True)

    if selected_rec:
        print(f"[CHAT] Scoped to resource: '{selected_rec.source}' (ID: {selected_rec.resource_id})")
        res_filter_id = selected_rec.resource_id
    else:
        print("[CHAT] Scoped across ALL ingested workspace content.")
        res_filter_id = None

    question = input("\nEnter your question: ").strip()
    if not question:
        print("[WARN] Empty question.")
        return

    print("[...] Generating answer...")
    try:
        result = engine.chat(question, resource_id=res_filter_id)
        print("\n[AI ANSWER]")
        print("=" * 60)
        print(result.answer)
        print("=" * 60)
        print(f"Grounded in Context : {'Yes [OK]' if result.was_grounded else 'No [FAIL]'}")
        if result.sources:
            print(f"Source Citations ({len(result.sources)} chunks used):")
            for doc in result.sources:
                src_name = doc.metadata.get("source", "unknown")
                page = doc.metadata.get("page")
                page_info = f" (page {page})" if page is not None else ""
                print(f"  - {src_name}{page_info}")
    except EngineError as exc:
        print(f"[ERROR] Chat error: {exc}")


def handle_summarize(engine: AIEngine) -> None:
    print("\n--- Generate Summary ---")
    selected_rec = select_resource(engine, allow_all=False)
    if not selected_rec:
        return

    force_regen = False
    cached_rec = engine._summary_cache.get(selected_rec.resource_id)
    if cached_rec:
        print(f"[INFO] Found cached summary for '{selected_rec.source}' (created {cached_rec.created_at[:19]}).")
        regen_choice = input("Do you want to [V]iew cached summary or [R]egenerate fresh? [V/R] (default: V): ").strip().lower()
        if regen_choice == "r":
            force_regen = True

    print(f"[...] {'Regenerating' if force_regen else 'Fetching/generating'} summary for '{selected_rec.source}'...")
    try:
        summary_text = engine.summarize(
            selected_rec.source, resource_id=selected_rec.resource_id, force_regenerate=force_regen
        )
        print("\n[DOCUMENT SUMMARY]")
        print("=" * 60)
        print(summary_text)
        print("=" * 60)
    except EngineError as exc:
        print(f"[ERROR] Summarization failed: {exc}")


def handle_generate_notes(engine: AIEngine) -> None:
    print("\n--- Generate Study Notes ---")
    selected_rec = select_resource(engine, allow_all=False)
    if not selected_rec:
        return

    style = input("Select note style [bullet / cornell] (default: bullet): ").strip().lower()
    if style not in ("bullet", "cornell"):
        style = "bullet"

    cached_rec = engine._summary_cache.get(selected_rec.resource_id)
    if cached_rec:
        print(f"[INFO] Reusing cached summary for '{selected_rec.source}' (0 extra summary LLM calls).")

    print(f"[...] Generating '{style}' study notes for '{selected_rec.source}'...")
    try:
        notes_text = engine.generate_notes(
            selected_rec.source, style=style, resource_id=selected_rec.resource_id
        )
        print(f"\n[STUDY NOTES - {style.upper()}]")
        print("=" * 60)
        print(notes_text)
        print("=" * 60)
    except EngineError as exc:
        print(f"[ERROR] Notes generation failed: {exc}")


def handle_generate_quiz(engine: AIEngine) -> None:
    print("\n--- Generate Multiple-Choice Quiz ---")
    selected_rec = select_resource(engine, allow_all=False)
    if not selected_rec:
        return

    count_str = input("Number of questions (default: 5): ").strip()
    q_count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 5

    diff = input("Difficulty [easy / medium / hard] (default: medium): ").strip().lower()
    if diff not in ("easy", "medium", "hard"):
        diff = "medium"

    cached_rec = engine._summary_cache.get(selected_rec.resource_id)
    if cached_rec:
        print(f"[INFO] Reusing cached summary for '{selected_rec.source}' (0 extra summary LLM calls).")

    print(f"[...] Generating {q_count} {diff}-difficulty quiz question(s) for '{selected_rec.source}'...")
    try:
        quiz_questions = engine.generate_quiz(
            selected_rec.source,
            question_count=q_count,
            difficulty=diff,
            resource_id=selected_rec.resource_id,
        )
        print(f"\n[GENERATED QUIZ - {len(quiz_questions)} Questions]")
        print("=" * 60)
        for i, q in enumerate(quiz_questions, 1):
            print(f"\nQ{i}: {q.question}")
            for opt_idx, opt in enumerate(q.options):
                prefix = "  [*]" if opt_idx == q.correct_answer_index else "  [ ]"
                option_letter = chr(65 + opt_idx)
                print(f"{prefix} {option_letter}. {opt}")
            print(f"Explanation: {q.explanation}")
    except EngineError as exc:
        print(f"[ERROR] Quiz generation failed: {exc}")


def main() -> None:
    print_banner()

    print("[STARTUP] Initializing AI Engine (loading embedding model & vector store)...")
    try:
        engine = AIEngine()
        engine.initialize()
        health = engine.health()
        print(f"[OK] AI Engine v{engine.version()} initialized successfully.")
        print(f"     Vector Store: {'Reachable' if health.vector_store_reachable else 'Unreachable'}")
        print(f"     Embeddings  : {'Loaded' if health.embedding_model_loaded else 'Not loaded'}")
    except Exception as exc:
        print(f"[CRITICAL ERROR] Initializing AI Engine failed: {exc}")
        sys.exit(1)

    while True:
        try:
            print_menu()
            choice = input("\nEnter menu choice (1-8): ").strip()
            if choice == "1":
                handle_add_pdf(engine)
            elif choice == "2":
                handle_add_youtube(engine)
            elif choice == "3":
                display_resources(engine.list_resources())
            elif choice == "4":
                handle_chat(engine)
            elif choice == "5":
                handle_summarize(engine)
            elif choice == "6":
                handle_generate_notes(engine)
            elif choice == "7":
                handle_generate_quiz(engine)
            elif choice == "8":
                print("\n[EXIT] Exiting StudyPilot AI Engine Demo. Goodbye!")
                break
            else:
                print("[ERROR] Invalid menu choice. Please enter a number from 1 to 8.")
        except KeyboardInterrupt:
            print("\n\n[EXIT] Interrupted by user. Exiting Demo.")
            break
        except Exception as exc:
            print(f"[ERROR] Unexpected error: {exc}")


if __name__ == "__main__":
    main()
