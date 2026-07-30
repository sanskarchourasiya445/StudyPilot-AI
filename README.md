# StudyPilot AI Engine

A framework-independent Retrieval-Augmented Generation (RAG) engine for personal study workspaces.

This package provides a single, well-documented Python package (`ai_engine`) that ingests PDFs, YouTube lectures, and text files, converts them into retrieval-ready chunks, stores them in a Chroma vector store, and exposes services for RAG chat, summarization, notes, and quiz generation.

## Project Overview

- What this project is: a reusable AI Engine that implements incremental ingestion, vectorization, and grounded LLM-driven services. It is intentionally framework-agnostic — designed to be imported by a web backend (FastAPI or similar) rather than being a full web app itself.
- Problem it solves: lets students build a searchable, chat-capable knowledge base from mixed media (PDFs, text, YouTube) so they can ask questions, get summaries, generate notes, and produce quizzes grounded in their own materials.
- Purpose: provide a clean, testable, and production-minded core implementation of a RAG pipeline suitable for extension and deployment as the backend for study-assist applications.

## Features

- PDF ingestion (per-page extraction)
- TXT file ingestion
- YouTube ingestion with two-tier transcription: captions-first, local Whisper fallback
- Text preprocessing and cleaning
- Chunking (retrieval-sized and summary-sized) using recursive character splitting
- Local embeddings via HuggingFace / sentence-transformers
- Chroma vector database for persistent, incremental ingestion
- MMR (Maximal Marginal Relevance) retriever with scoping filters
- RAG-style chat service (retrieve -> prompt -> Gemini LLM generate)
- Map-reduce summarization service
- Notes generation service (composes summarization)
- Quiz generation service (structured JSON output, code-fence tolerant)
- Resource lifecycle management: `resource_id` per ingest, `list`, `get`, `delete`, and per-resource stats
- Raw search (retrieval-only) endpoint (no LLM call)
- Health and version introspection
- Structured logging and domain-specific exceptions
- Unit tests covering core functionality

Only features implemented in the current codebase are listed above.

## Project Architecture

High level flow:

1. Source (PDF / TXT / YouTube URL) is routed to the appropriate loader via `ai_engine.loaders.loader_factory`.
2. Loader returns LangChain `Document` objects: per-page for PDFs, single transcript document for YouTube/TXT.
3. Preprocessing: `cleaner` normalizes text; `chunker` splits documents into retrieval- and summary-sized chunks; `metadata` enriches chunks with `resource_id`, `workspace_id`, `user_id`, `chunk_index`, and timestamps.
4. Embeddings: a cached HuggingFace `Embeddings` model produces vectors (via `ai_engine.embeddings.embedding_model` / `embedder`).
5. Vector store: `ai_engine.vectorstore.chroma` opens a persistent Chroma collection and supports incremental `add_documents`, retrieval, and resource lifecycle operations.
6. Retrieval: `ai_engine.vectorstore.retriever` builds an MMR retriever with optional scoping filters (source/resource/workspace/user) and returns relevant chunks.
7. LLM: `ai_engine.llm.gemini.GeminiLLM` wraps the `google-genai` client and exposes a simple `generate(prompt)` API.
8. Services: `ChatService`, `SummaryService`, `NotesService`, and `QuizService` orchestrate retrieval, prompting (via `ai_engine.llm.prompts`), and LLM calls.

Core modules and responsibilities:

- `ai_engine/engine.py` — the public facade (`AIEngine`) that a backend should import. Handles initialization (embedding model, vector store, LLM) and exposes `ingest`, `chat`, `search`, `summarize`, `generate_notes`, `generate_quiz`, resource management, `health`, and `version`.
- `ai_engine/loaders` — Strategy-pattern loaders for each source type: PDF, TXT, YouTube (captures captions first, Whisper fallback).
- `ai_engine/preprocessing` — text cleaning, chunking, and metadata enrichment.
- `ai_engine/embeddings` — loading/caching the HF embedding model and a small `Embedder` wrapper.
- `ai_engine/vectorstore` — single file that encapsulates Chroma interactions, incremental ingestion, and resource lifecycle.
- `ai_engine/llm` — Gemini client wrapper and centralized prompt templates.
- `ai_engine/services` — user-facing capabilities built on top of retrieval + LLM.
- `ai_engine/utils` — shared helpers, logger configuration, and custom exceptions.

Data flow (concise):

Source -> Loader -> Cleaner -> Chunker -> Metadata enrichment -> Embedding -> Chroma (persist) -> Retriever -> Prompt -> Gemini -> Service response

## Installation

1. Create a Python 3.10+ virtual environment.
2. Install pinned dependencies:

```bash
pip install -r requirements.txt
```

## Environment

Create a `.env` at the project root with your Gemini API key:

```
GOOGLE_API_KEY=your-key-here
```

Note: local Whisper transcription requires `openai-whisper` and `torch`; these are optional unless you intend to use YouTube Whisper fallback.

## Quick Usage

Minimal interactive example:

```python
from ai_engine.engine import AIEngine

engine = AIEngine()
engine.initialize()

# Ingest a PDF or YouTube URL
res = engine.ingest('lecture_notes.pdf')
print('Resource ID:', res.resource_id)

# Chat
resp = engine.chat('What did the lecture say about gradient descent?')
print(resp.answer)
```

See `test_engine.py` and `ai_engine/tests/` for examples and unit tests.

## Tests

Run the test suite with `pytest`:

```bash
pytest -q
```

## Contributing

This project aims to be minimal and extensible. If you add features, prefer:

- keeping `AIEngine` as the single public facade
- adding new loaders under `ai_engine/loaders` and registering them in `loader_factory.py`
- keeping provider keys local to their adapter (e.g. LLM files load their own env vars)

If you'd like, I can also:

- run tests locally and fix minor style issues
- add a `CONTRIBUTING.md` and `CODE_OF_CONDUCT`

---
Generated by repository analysis. If you want a shorter README variant or additional sections (API examples, OpenAPI snippets, deployment tips), tell me which ones to add.
