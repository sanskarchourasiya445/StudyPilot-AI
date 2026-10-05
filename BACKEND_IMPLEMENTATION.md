# StudyPilot Backend Specification

## 1. Purpose

Build the complete backend for **StudyPilot**, an AI-powered personalized study platform.

The existing **StudyPilot AI Engine is already implemented, tested, and considered the stable AI core**.

The backend's responsibility is to expose the AI Engine through secure, well-structured APIs and manage application data, users, resources, conversations, summaries, notes, quizzes, and persistence.

### Critical principle

**Do NOT rebuild, redesign, or duplicate the AI Engine.**

The backend must import and use the existing:

```python
from ai_engine.engine import AIEngine
```

The AI Engine remains framework-independent.

---

# 2. Existing AI Engine

The current AI Engine already provides:

* PDF ingestion
* TXT ingestion
* YouTube ingestion
* captions-first YouTube processing
* Whisper fallback
* preprocessing
* chunking
* metadata enrichment
* HuggingFace embeddings
* Chroma vector storage
* MMR retrieval
* resource filtering
* RAG chat
* grounding and source citations
* summarization
* notes generation
* quiz generation
* resource management
* search
* health
* version
* summary caching
* cache invalidation
* force regeneration
* domain-specific exceptions

The backend must consume these capabilities rather than implement another RAG pipeline.

---

# 3. Backend Technology Stack

Use:

### Backend

* **Python 3.11+**
* **FastAPI**
* **Uvicorn**
* **Pydantic v2**
* **pydantic-settings**

### Database

* **PostgreSQL**
* **SQLAlchemy 2.x**
* **Alembic**

Do NOT introduce Prisma for the Python backend.

### Authentication

Use:

* JWT-based authentication
* password hashing using a secure password hashing library
* access tokens
* refresh-token strategy if appropriate

Authentication must be designed so that every protected resource belongs to the authenticated user.

### Testing

* pytest
* pytest-asyncio
* httpx/TestClient
* database-isolated tests

### Development

* `.env`
* `.env.example`
* structured logging
* clear configuration management

### Future infrastructure

Design the backend so it can later support:

* Redis
* background workers
* object storage
* Docker
* CI/CD
* AWS

Do NOT add these services unless they are actually required by the current implementation.

---

# 4. Backend Architecture

Use a clean layered architecture.

Recommended structure:

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── resources.py
│   │   │   ├── chat.py
│   │   │   ├── study.py
│   │   │   ├── conversations.py
│   │   │   └── health.py
│   │   │
│   │   └── deps.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   └── models/
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── resource.py
│   │   ├── chat.py
│   │   ├── conversation.py
│   │   ├── summary.py
│   │   ├── notes.py
│   │   └── quiz.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── resource_service.py
│   │   ├── chat_service.py
│   │   ├── study_service.py
│   │   └── conversation_service.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── resource_repository.py
│   │   ├── conversation_repository.py
│   │   └── study_repository.py
│   │
│   └── ai/
│       └── engine_provider.py
│
├── tests/
│
├── alembic/
├── alembic.ini
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

The exact structure may be adjusted if the existing repository has a better established convention, but maintain separation of concerns.

---

# 5. Layer Responsibilities

## API Layer

Responsible for:

* HTTP
* request validation
* authentication dependencies
* response schemas
* HTTP status codes

Routes must NOT contain business logic.

## Service Layer

Responsible for:

* application business logic
* orchestration
* AI Engine interaction
* transactions where appropriate

## Repository Layer

Responsible for:

* database queries
* CRUD operations
* persistence logic

## AI Integration Layer

Responsible for:

* creating/reusing AIEngine
* translating backend requests into AIEngine calls
* converting AIEngine results into application-level responses

Do not duplicate AI Engine functionality here.

---

# 6. Database Design

Use PostgreSQL for application state.

The database should contain at minimum:

## users

```text
id
email
password_hash
name
created_at
updated_at
```

## resources

```text
id
user_id
resource_id
source
source_type
title
workspace_id
status
metadata
created_at
updated_at
```

`resource_id` must correspond correctly with the AI Engine resource identity.

Do NOT use filename/source alone as the unique identifier.

## conversations

```text
id
user_id
resource_id nullable
title
created_at
updated_at
```

## messages

```text
id
conversation_id
role
content
created_at
```

## summaries

```text
id
resource_id
summary
version
config_hash
created_at
updated_at
```

## notes

```text
id
resource_id
style
content
created_at
updated_at
```

## quizzes

```text
id
resource_id
difficulty
question_count
data
created_at
updated_at
```

Use proper foreign keys and indexes.

---

# 7. Resource Ownership and Security

This is critical.

A user must only be able to access their own resources.

Every protected operation must validate ownership:

```text
authenticated user
        ↓
resource lookup
        ↓
verify resource.user_id
        ↓
allow operation
```

Never trust a `user_id` supplied by the client.

Derive the authenticated user from the authentication context.

Prevent:

* cross-user resource access
* cross-user conversations
* cross-user summaries
* cross-user notes
* cross-user quizzes

---

# 8. Authentication APIs

Implement:

```http
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

Request/response schemas must be strongly validated.

Passwords must never be stored in plaintext.

Do not return password hashes.

---

# 9. Resource APIs

Implement:

```http
POST   /api/resources/pdf
POST   /api/resources/youtube
GET    /api/resources
GET    /api/resources/{resource_id}
DELETE /api/resources/{resource_id}
```

## PDF upload

Accept multipart file upload.

Validate:

* extension
* content type
* size limits
* empty uploads

Store the uploaded file safely.

Then call:

```python
engine.ingest(...)
```

Associate the returned AI Engine `resource_id` with the authenticated user in PostgreSQL.

Return:

* resource ID
* source
* source type
* status
* metadata

## YouTube

Accept a YouTube URL.

Validate the input.

Call:

```python
engine.ingest(url)
```

Persist the resulting resource information.

---

# 10. Resource Status

Resources should have clear states such as:

```text
processing
ready
failed
deleted
```

For operations that may take significant time, the API should not pretend the operation is complete before it actually is.

For the initial implementation, synchronous processing is acceptable if it remains reliable.

Design the service layer so that background processing can be introduced later without rewriting the API contract.

---

# 11. Chat API

Implement:

```http
POST /api/chat
```

Request:

```json
{
  "message": "Explain MongoDB concepts",
  "resource_id": "optional",
  "conversation_id": "optional"
}
```

Behavior:

* verify authenticated user
* verify resource ownership when `resource_id` is provided
* call existing `engine.chat()`
* pass the correct `resource_id`
* return answer
* return grounding information
* return source citations

Do NOT perform retrieval directly from the backend.

The AI Engine owns retrieval.

---

# 12. Conversations

Conversation persistence belongs to the backend.

Flow:

```text
User message
     ↓
Create/load conversation
     ↓
Persist user message
     ↓
AI Engine chat
     ↓
Persist assistant response
     ↓
Return response
```

Implement:

```http
POST /api/conversations
GET  /api/conversations
GET  /api/conversations/{conversation_id}
GET  /api/conversations/{conversation_id}/messages
DELETE /api/conversations/{conversation_id}
```

Support conversations scoped to a resource where appropriate.

---

# 13. Summary API

Implement:

```http
POST /api/resources/{resource_id}/summary
GET  /api/resources/{resource_id}/summary
```

Behavior:

1. Verify resource ownership.
2. Check backend-persisted summary if available.
3. Otherwise call the AI Engine.
4. Store the generated summary.
5. Return it.

Support explicit regeneration:

```json
{
  "force_regenerate": true
}
```

Do not generate a new summary every time the user opens the summary page.

---

# 14. Notes API

Implement:

```http
POST /api/resources/{resource_id}/notes
GET  /api/resources/{resource_id}/notes
```

Notes should reuse the existing generated summary whenever possible.

The backend should not trigger another full summarization unnecessarily.

Support styles supported by the AI Engine.

---

# 15. Quiz API

Implement:

```http
POST /api/resources/{resource_id}/quiz
GET  /api/resources/{resource_id}/quizzes
```

Request should support:

```json
{
  "question_count": 5,
  "difficulty": "medium"
}
```

Reuse the existing summary when appropriate.

Return structured quiz questions rather than raw model JSON.

---

# 16. Search API

Expose retrieval-only functionality:

```http
POST /api/resources/{resource_id}/search
```

This should call the existing:

```python
engine.search(...)
```

Do not implement a second search system in the backend.

---

# 17. Health API

Implement:

```http
GET /api/health
```

Return:

* backend status
* database connectivity
* AI Engine health
* engine version

Do not expose secrets.

---

# 18. Error Handling

Create a centralized exception-handling strategy.

Map:

```text
validation error → 400 / 422
authentication failure → 401
authorization failure → 403
resource not found → 404
AI Engine failure → appropriate 5xx/4xx
external service failure → 503
database failure → 500/503
rate/quota error → clear 429/503 response
```

Never expose raw stack traces to API clients.

Log internal errors with useful diagnostic information.

---

# 19. AI Engine Error Mapping

The AI Engine already defines domain-specific exceptions.

The backend should translate them into appropriate HTTP responses rather than replacing or duplicating them.

For example:

```text
ResourceNotFoundError
        ↓
HTTP 404
```

```text
SearchError
        ↓
HTTP 500/503 depending on cause
```

```text
Gemini quota/rate error
        ↓
HTTP 429 or 503
```

---

# 20. Configuration

Create:

```text
.env.example
```

Include placeholders for:

```env
DATABASE_URL=
GEMINI_API_KEY=
JWT_SECRET=
JWT_ALGORITHM=
ACCESS_TOKEN_EXPIRE_MINUTES=
```

Never commit the real `.env`.

Use `pydantic-settings` for configuration.

Do not scatter environment-variable reads throughout the application.

---

# 21. Database Migrations

Use Alembic.

The workflow must support:

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```

Do not manually modify database schema outside migrations.

---

# 22. Testing Strategy

Build tests at multiple levels.

## Unit tests

Test:

* services
* repositories
* authentication
* validation
* ownership checks

## API tests

Test:

* registration
* login
* protected endpoints
* resource ownership
* chat
* summaries
* notes
* quizzes
* error responses

## AI integration tests

Mock the AI Engine where appropriate.

Do not make real Gemini API calls in normal automated tests.

---

# 23. API Documentation

FastAPI's OpenAPI documentation should work.

Every endpoint must have:

* clear summary
* request schema
* response schema
* status codes
* authentication requirements

The backend should be understandable through `/docs`.

---

# 24. Performance

Do not prematurely introduce complex infrastructure.

Initial goals:

* reuse a single properly managed AIEngine instance per application process
* avoid repeated initialization of embedding models
* avoid repeated summary generation
* use database indexes on ownership and resource lookups
* avoid N+1 database queries
* avoid loading entire large datasets unnecessarily

Long-running ingestion and AI operations should be designed so they can later move to background workers.

---

# 25. Security

Implement at minimum:

* password hashing
* JWT authentication
* authorization checks
* input validation
* file validation
* upload size limits
* safe file names
* no secret leakage
* no raw exception exposure
* database parameterization through SQLAlchemy
* CORS configuration through environment/configuration
* secure HTTP behavior suitable for deployment

Do not implement security features merely as placeholders.

---

# 26. Logging

Use structured application logging.

Log important events such as:

```text
user registration
login
resource ingestion started
resource ingestion completed
resource ingestion failed
chat request
summary generation
notes generation
quiz generation
database failures
AI Engine failures
```

Never log:

* API keys
* passwords
* JWT secrets
* sensitive authentication data

---

# 27. What NOT to Build Yet

Do NOT add these unless they become necessary:

* Redis
* Celery
* Kafka
* Kubernetes
* microservices
* multiple databases
* GraphQL
* event-driven architecture
* service mesh
* unnecessary abstractions

The initial backend should be a **well-structured modular monolith**.

That is intentional.

---

# 28. Backend Development Phases

Implement in this order.

## Phase 1 — Foundation

* backend project structure
* FastAPI
* configuration
* database connection
* SQLAlchemy
* Alembic
* health endpoint
* logging

## Phase 2 — Authentication

* User model
* registration
* login
* JWT
* authentication dependencies
* ownership checks

## Phase 3 — Resources

* Resource model
* PDF upload
* YouTube ingestion
* resource listing
* resource details
* deletion

## Phase 4 — AI Integration

* AIEngine provider
* chat API
* search API
* summary API
* notes API
* quiz API

## Phase 5 — Conversations

* conversations
* messages
* persistent chat history

## Phase 6 — Reliability

* centralized errors
* validation
* rate/quota handling
* logging
* integration tests

## Phase 7 — API Quality

* OpenAPI documentation
* response consistency
* pagination where appropriate
* cleanup
* performance review

---

# 29. Definition of Done

The backend is considered complete when:

### Architecture

* clean modular-monolith structure
* clear separation of responsibilities
* AI Engine remains independent

### Authentication

* user registration works
* login works
* protected endpoints require authentication
* users cannot access other users' resources

### Resources

* PDF upload works
* YouTube ingestion works
* resources persist in PostgreSQL
* AI Engine resources remain correctly mapped

### AI

* chat works
* resource-scoped chat works
* search works
* summary works
* summary persistence works
* notes work
* quizzes work

### Conversations

* conversations persist
* messages persist
* chat history can be retrieved

### Database

* migrations work
* schema is consistent
* indexes exist where needed

### Testing

* unit tests pass
* API tests pass
* AI integration tests use safe mocks where appropriate

### Documentation

* API documentation works
* README explains setup and architecture
* `.env.example` exists

---

# 30. Critical Implementation Rules

1. **Do not modify the existing AI Engine unless a genuine integration bug is discovered.**
2. **Do not duplicate RAG logic in the backend.**
3. **Do not bypass the AIEngine facade.**
4. **Do not trust user-supplied ownership IDs.**
5. **Do not store secrets in source code.**
6. **Do not add infrastructure without a concrete requirement.**
7. **Do not sacrifice correctness for speed.**
8. **Use migrations for database changes.**
9. **Test every major feature.**
10. **Keep the system modular so future Docker/AWS/DevOps work is straightforward.**

---

# 31. Required First Step

Before writing backend code:

1. Inspect the existing repository.
2. Inspect the current AI Engine APIs and documentation.
3. Inspect `AI_ENGINE_README.md`.
4. Inspect `DEVELOPMENT_GUIDE.MD`.
5. Inspect `engine.py` public methods and return types.
6. Inspect existing tests.
7. Produce a backend architecture and implementation plan.
8. Identify any integration constraints.
9. Do not modify the existing AI Engine.

Only begin implementation after the backend plan is internally consistent with the existing AI Engine.

---

# Final Goal

Turn the existing StudyPilot AI Engine into a complete backend-powered application:

```text
                    StudyPilot
                        │
                 React Frontend
                        │
                    FastAPI
                        │
          ┌─────────────┴─────────────┐
          │                           │
     PostgreSQL                    AI Engine
          │                     ┌──────┼──────┐
          │                     │      │      │
     Application data         Chroma Gemini Embeddings
          │
    Users / Resources
    Conversations
    Messages
    Summaries
    Notes
    Quizzes
```

Build a **production-minded modular monolith**, not a collection of disconnected endpoints.

The backend must make the existing AI Engine accessible, persistent, secure, testable, and ready for the future React frontend.


Read `BACKEND_SPEC.md` completely before making any changes.

Also inspect the existing StudyPilot AI Engine, especially:

* `ai_engine/engine.py`
* `AI_ENGINE_README.md`
* `DEVELOPMENT_GUIDE.MD`
* existing tests

Do not modify the AI Engine.

First produce a complete backend architecture and implementation plan that follows `BACKEND_SPEC.md` and is compatible with the existing AI Engine APIs.

The plan must include:

* backend folder structure
* database schema
* API endpoints
* authentication flow
* AI Engine integration
* resource ownership/security
* summary persistence/cache strategy
* conversation/message architecture
* testing strategy
* migration strategy

Do not implement anything yet. I want to review the architecture and plan first.
