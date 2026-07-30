# StudyPilot AI Engine

A framework-independent AI Engine for a personalized learning workspace.
Students ingest PDFs, YouTube lectures, and text files; the engine turns
all of them into one shared, chattable knowledge base and can also
summarize, take notes, and generate quizzes from anything ingested.

This package contains **no FastAPI, no database, no auth, no frontend
code** — it is designed to be imported wholesale by a future API layer.

## Architecture

```
PDF ----\
         \
TXT ------> clean -> chunk -> enrich metadata -> embed -> Chroma -> MMR retriever -> Gemini -> Response
         /
YouTube -/
   |
   +-- captions (youtube-transcript-api), fast path
   +-- audio download + Whisper, fallback path
```

Everything after loading is shared across all three source types —
different resources only ever differ in their **loader**
(`loaders/pdf_loader.py`, `loaders/youtube_loader.py`,
`loaders/txt_loader.py`), selected automatically by
`loaders/loader_factory.py`.

```
ai_engine/
├── engine.py              # AIEngine facade — the ONLY class a FastAPI layer should import
├── config.py               # single source of tunable constants
│
├── loaders/                # source -> Document (Strategy pattern)
│   ├── base_loader.py
│   ├── pdf_loader.py
│   ├── youtube_loader.py
│   ├── txt_loader.py
│   └── loader_factory.py
│
├── youtube/                 # YouTube-specific subsystem
│   ├── extractor.py          # captions + metadata (no download)
│   ├── audio_processor.py    # download/normalize/chunk audio (fallback)
│   └── transcriber.py        # local Whisper transcription (fallback)
│
├── preprocessing/           # shared for every source type
│   ├── cleaner.py
│   ├── chunker.py
│   └── metadata.py
│
├── embeddings/
│   ├── embedding_model.py    # cached HuggingFace embedding singleton
│   └── embedder.py           # domain-facing embed_documents/embed_query
│
├── vectorstore/
│   ├── chroma.py             # incremental ingestion, per-source fetch
│   └── retriever.py          # MMR retriever, optional per-source filter
│
├── llm/
│   ├── prompts.py            # every prompt template, in one place
│   └── gemini.py             # Gemini client wrapper
│
├── services/                 # one class per user-facing capability
│   ├── chat_service.py
│   ├── summary_service.py    # map-reduce summarization
│   ├── notes_service.py      # composes SummaryService
│   └── quiz_service.py       # composes SummaryService, parses JSON output
│
├── utils/
│   ├── exceptions.py          # AIEngineError, ConfigurationError, etc.
│   ├── logger.py               # one-time logging configuration
│   └── helpers.py               # URL detection, cleaning, formatting
│
└── tests/
    ├── test_pdf.py
    ├── test_youtube.py
    └── test_chat.py
```

## Design notes worth knowing before extending this

- **Incremental ingestion, not one-shot.** `vectorstore/chroma.py` is
  built around `add_documents()` being called once per upload, since a
  student's workspace grows over time — not a single corpus embedded
  once at startup.
- **Per-source filtering.** `vectorstore/retriever.py` accepts a
  `source_filter` so a student can chat with, summarize, take notes on,
  or quiz themselves on ONE uploaded item instead of the whole
  workspace.
- **Gemini-only, by design, for now.** `llm/gemini.py` is a standalone
  class rather than an ABC + factory (unlike some multi-provider RAG
  reference implementations) because only Gemini is in scope. Every
  service depends on it via constructor injection, so adding a second
  provider later means introducing a `BaseLLM` interface and a factory
  — no service call site changes.
- **YouTube uses captions first, Whisper as fallback.**
  `youtube/extractor.py` tries `youtube-transcript-api` first (fast,
  free, no download); `loaders/youtube_loader.py` falls back to
  `youtube/audio_processor.py` + `youtube/transcriber.py` (yt-dlp +
  local Whisper) only when no caption track exists.
- **Notes and quiz generation reuse summarization**, via composition
  (`NotesService` and `QuizService` each hold a `SummaryService`), so
  arbitrarily long source material is condensed the same way everywhere
  rather than re-implementing map-reduce per service.

## Running tests

```bash
pip install -r requirements.txt
pytest ai_engine/tests/ -v
```

## Environment variables

Create a `.env` file at the project root:

```
GEMINI_API_KEY=your-key-here
```

## v1.1 changelog (additive, 100% backward compatible)

Every v1.0 method signature and behavior is unchanged for callers that
don't pass the new optional arguments. What's new:

| Area | Change |
|---|---|
| `ingest(source, workspace_id=None, user_id=None)` | Now generates and returns a `resource_id` in `IngestionResult`. `workspace_id`/`user_id` are optional scoping tags. |
| Chunk metadata | Every chunk now also carries `resource_id`, `workspace_id`, `user_id`, `resource_type` (mirrors `source_type`), `uploaded_at` (mirrors `ingested_at`), and `page` (defaulted to `None` where not applicable). `chunk_index` is now counted per `resource_id` instead of per `source` - this fixes a real cross-resource collision bug where two resources sharing the same filename/title would previously share one chunk_index sequence. |
| `chat(question, source_filter=None, resource_id=None, workspace_id=None, user_id=None)` | New optional filters, composable together. |
| `search(query, ...)` | **New.** Raw retrieval - returns matching chunks without an LLM call. |
| `delete_resource(resource_id)` | **New.** Removes every chunk belonging to one resource. |
| `list_resources()` | **New.** Returns a `ResourceRecord` per ingested resource. |
| `get_resource(resource_id)` | **New.** Fetch one resource's record. |
| `stats(resource_id)` | **New.** Character/chunk-count statistics for one resource. |
| `workspace_stats(workspace_id=None)` | **New.** Aggregate stats across a workspace (or the whole store). |
| `health()` | **New.** Safe to call anytime, even before `initialize()`. |
| `version()` | **New.** Returns `config.ENGINE_VERSION`. |
| Exceptions | `ResourceManagementError` and `SearchError` added (both subclass `EngineError`, so existing `except EngineError` handling still catches them). `ResourceNotFoundError` added at the vector-store layer (subclasses `VectorStoreError`). |

Files touched: `config.py`, `utils/helpers.py`, `preprocessing/metadata.py`,
`vectorstore/chroma.py`, `vectorstore/retriever.py`, `engine.py`. No
folders were renamed, no existing method was removed or had its
signature narrowed. Three new test files
(`test_metadata_v1_1.py`, `test_vectorstore_resources_v1_1.py`,
`test_engine_v1_1.py`) cover all of the above; all 17 original tests
still pass unmodified (63/63 total).

**Known limitation carried over, not in scope of this release:** `summarize()`,
`generate_notes()`, and `generate_quiz()` still key off `source` (not
`resource_id`) internally via `get_documents_by_source`. This means they
still have the filename/title-collision exposure described above. A
natural v1.2 candidate would be adding `resource_id`-based overloads of
these three methods once the consuming backend is ready to pass
`resource_id` instead of `source`.

## Minimal usage example

```python
from ai_engine.engine import AIEngine

engine = AIEngine()
engine.initialize()

engine.ingest("lecture_notes.pdf")
engine.ingest("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

result = engine.chat("What did the lecture say about gradient descent?")
print(result.answer)

summary = engine.summarize("lecture_notes.pdf")
notes = engine.generate_notes("lecture_notes.pdf", style="cornell")
quiz = engine.generate_quiz("lecture_notes.pdf", question_count=5, difficulty="medium")
```