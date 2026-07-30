You are a Senior Python Software Architect, Staff AI Engineer, and Code Reviewer.

Your task is NOT to add new features or redesign the project.

Your task is to perform a complete engineering audit of my AI Engine and ensure that everything works correctly.

This repository is a framework-independent AI Engine for StudyPilot that supports:

- PDF ingestion
- TXT ingestion
- YouTube ingestion
- Chroma vector database
- HuggingFace embeddings
- Gemini LLM
- RAG Chat
- Summarization
- Notes generation
- Quiz generation
- Resource management
- Search
- Health checks
- Unit tests

The README and AI_ENGINE_README describe the intended architecture. Treat those documents as the expected specification.

I want you to verify that the actual implementation matches the documentation.

--------------------------------------------------
PHASE 1 — Repository Audit
--------------------------------------------------

Inspect every folder, every module, every public API, and every dependency.

Check:

- imports
- package structure
- circular imports
- dead code
- duplicated logic
- incorrect naming
- broken references
- inconsistent architecture
- unused dependencies
- incorrect configuration
- missing __init__.py files
- invalid relative imports
- type hint problems
- lint issues
- exception handling
- logging consistency

Do not rewrite architecture.

Only identify real implementation problems.

--------------------------------------------------
PHASE 2 — Functional Verification
--------------------------------------------------

Verify that every public AIEngine method actually works.

Check:

initialize()

ingest()

chat()

search()

summarize()

generate_notes()

generate_quiz()

list_resources()

get_resource()

delete_resource()

stats()

workspace_stats()

health()

version()

Ensure every documented feature behaves correctly.

--------------------------------------------------
PHASE 3 — Pipeline Validation
--------------------------------------------------

Verify the entire RAG pipeline.

Loader
↓

Cleaner

↓

Chunker

↓

Metadata

↓

Embeddings

↓

Vector Store

↓

Retriever

↓

Prompt Builder

↓

Gemini

↓

Response

Ensure every stage integrates correctly.

--------------------------------------------------
PHASE 4 — Loader Validation
--------------------------------------------------

Test every loader.

PDF Loader

- corrupted PDFs
- empty PDFs
- multiple pages
- metadata

TXT Loader

- UTF-8
- empty files
- large files

YouTube Loader

- transcript available
- transcript unavailable
- Whisper fallback
- invalid URLs
- deleted videos
- private videos

--------------------------------------------------
PHASE 5 — Vector Store Validation
--------------------------------------------------

Verify:

incremental ingestion

duplicate handling

resource deletion

resource lookup

metadata integrity

resource_id

workspace_id

user_id

chunk_index

source filtering

search filtering

collection persistence

--------------------------------------------------
PHASE 6 — Service Validation
--------------------------------------------------

Check:

ChatService

SummaryService

NotesService

QuizService

Verify prompt formatting.

Verify returned data.

Verify JSON parsing.

Verify failures.

--------------------------------------------------
PHASE 7 — Testing
--------------------------------------------------

Run every existing test.

Create additional tests ONLY where functionality is missing.

Never remove tests.

If a test fails,

find the root cause,

fix it,

rerun.

Repeat until every test passes.

--------------------------------------------------
PHASE 8 — Documentation Validation
--------------------------------------------------

Compare implementation against

README.md

AI_ENGINE_README.md

Report any mismatch.

If documentation is correct,

change code.

If code is correct,

update documentation.

Keep both synchronized.

--------------------------------------------------
PHASE 9 — Dependency Audit
--------------------------------------------------

Check every dependency.

Identify

deprecated packages

security issues

better maintained alternatives

breaking changes

For example:

google.generativeai

langchain-community

etc.

Only replace packages if migration is safe.

--------------------------------------------------
PHASE 10 — Production Readiness
--------------------------------------------------

Evaluate

configuration

logging

resource cleanup

memory usage

error handling

thread safety

temporary files

FFmpeg detection

Whisper fallback

embedding caching

Chroma persistence

environment loading

startup time

shutdown cleanup

--------------------------------------------------
IMPORTANT RULES
--------------------------------------------------

DO NOT redesign the project.

DO NOT add unnecessary abstractions.

DO NOT change the public API unless there is a real bug.

Preserve backward compatibility.

Keep architecture exactly the same.

Every change must have a technical reason.

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------

For every issue found provide:

1. Severity
   Critical / High / Medium / Low

2. File

3. Root Cause

4. Why it is a problem

5. Exact Fix

6. Apply the fix

7. Verify it works

8. Continue auditing.

Do not stop until the repository has been completely audited.

The goal is to leave the repository in a production-quality state while preserving its current architecture.