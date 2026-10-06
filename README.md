# StudyPilot AI


> **A High-Precision, Multi-Source RAG Personalized Learning Workspace**  
> Ingest academic PDFs and YouTube lecture transcripts into an interactive, grounded study platform featuring contextual Q&A, structured notes, AI summaries, and practice quizzes.

---

## Overview

**StudyPilot AI** is an end-to-end Retrieval-Augmented Generation (RAG) learning assistant engineered to bridge academic course materials with personalized study workflows. Students can ingest lecture PDFs and YouTube video lectures, transforming fragmented course content into a unified, searchable, and interactive knowledge base.

Unlike generic chatbot wrappers, StudyPilot AI uses a dual-database architecture, local sentence embeddings, MMR-based retrieval, conversational query rewriting, and strict anti-hallucination prompt constraints with exact source-level citation tracking.

### Core Capabilities

- **Multi-Source Material Ingestion**: Ingests textbook chapters, syllabus notes, and lecture slide PDFs (with page-level chunking) alongside YouTube video lectures (via caption transcripts with automated timestamping).
- **Multi-Resource Study Scope**: Query individual documents or scope retrieval across entire course units or multiple distinct resources simultaneously.
- **Contextual Follow-up Query Understanding**: Automatically rewrites elliptical follow-up questions (e.g., *"What are its main advantages?"*) into self-contained retrieval queries using recent conversation context before vector search.
- **Grounded Q&A with Strict Citations**: Enforces strict grounding rules. Answers must cite exact source names, page numbers, or lecture timestamps; queries unsupported by ingested material gracefully indicate lack of context rather than hallucinating.
- **AI Study Suite**:
  - **Structured Summaries**: Key takeaways, core concepts, and comprehensive topic overviews with caching.
  - **Study Notes**: Generates notes formatted in Cornell Method or Structured Outline styles.
  - **Adaptive Practice Quizzes**: Generates multi-question diagnostic quizzes with options, correct answer keys, and conceptual explanations.
  - **Quiz Evaluation**: Automatically scores submitted answers, explains mistakes, and updates mastery schedules.
- **Conversation Persistence**: Full conversation history tracking, session resumption, and topic switching across study sessions.
- **Robust UI System**: React 19 single-page application with responsive layouts, customizable Dark / Light / System theme modes, and an intuitive study workspace.

---

## System Architecture

StudyPilot AI cleanly decouples relational application state from vector similarity search:

```
┌────────────────────────────────────────────────────────┐
│                   React 19 Frontend                    │
│     (Vite + Tailwind CSS v4 + React Router + Lucide)   │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP / JSON (Axios)
                            ▼
┌────────────────────────────────────────────────────────┐
│                   FastAPI Backend                      │
│   ├── Authentication & User Management (JWT + Bcrypt)  │
│   ├── Resource Ingestion & Lifecycle Management       │
│   ├── Study Tool Endpoints (Summary, Notes, Quiz)      │
│   ├── Conversation & Message Persistence               │
│   └── Mastery & Spaced Repetition Scheduling           │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
       SQLAlchemy (psycopg2)             │ Internal Python API
                ▼                        ▼
┌──────────────────────────────┐ ┌──────────────────────────────────┐
│     PostgreSQL Database      │ │      AI Engine Core Package      │
│  - Users & Passwords         │ │  ├── Document Loaders            │
│  - Resources & Metadata      │ │  │   (PyPDF, YouTube Captions)   │
│  - Conversations & Messages  │ │  ├── Preprocessing & Chunking    │
│  - Summaries, Notes, Quizzes │ │  ├── HuggingFace MiniLM Embedder │
│  - Quiz Attempts & Mastery   │ │  ├── ChromaDB Vector Store       │
└──────────────────────────────┘ │  ├── Contextual Query Rewriter   │
                                 │  └── Gemini LLM Generator        │
                                 └──────────────────────────────────┘
```

### PostgreSQL vs. ChromaDB: Data Division of Labor

| Concern | Database Engine | Responsibilities |
| :--- | :--- | :--- |
| **Relational Data** | **PostgreSQL** | User accounts, hashed credentials, resource metadata, conversation histories, persisted chat turns, generated summaries, notes, quiz structures, student submissions, and mastery tracking. |
| **Vector Search** | **ChromaDB** | Embedding vectors (384 dimensions), raw text chunks, and metadata filtering attributes (`user_id`, `resource_id`, `source`, `page`, `start_time`). |

---

## RAG Pipeline Architecture

```
1. INGESTION
   PDF Files ────────────────► PyPDF Loader ──────────────┐
   YouTube URLs ─────────────► Transcript API Loader ─────┤
                                                          ▼
2. PREPROCESSING                                    Raw Documents
   Clean text ──► Recursive Chunking (500 chars, 50 overlap)
                                                          ▼
3. EMBEDDINGS & STORAGE                           Enriched Chunks
   Hugging Face 'all-MiniLM-L6-v2' (CPU local) ──► ChromaDB Vector Store
                                                          ▼
4. QUERY PROCESSING                               User Question
   If conversational follow-up ──► LLM Contextual Rewriter
                                                          ▼
5. RETRIEVAL                                    Standalone Query
   ChromaDB MMR Search (top_k=4, fetch_k=20, lambda=0.7, metadata filtered)
                                                          ▼
6. GROUNDED GENERATION                          Retrieved Chunks + Prompt
   Google Gemini 2.5 Flash ──► Grounded Response + Inline Source Citations
```

### Pipeline Steps in Detail

1. **Ingestion**: PDFs are parsed using `PyPDFLoader` to extract page-by-page text. YouTube links are processed via `youtube-transcript-api` to extract timestamped subtitle segments.
2. **Chunking & Metadata**: Text is segmented with a recursive character splitter into 500-character chunks with a 50-character overlap. Each chunk is tagged with `resource_id`, `user_id`, `source`, and `page` or `start_time`.
3. **Embeddings**: Chunks are converted to dense vector embeddings using `sentence-transformers/all-MiniLM-L6-v2` running locally on CPU.
4. **Vector Storage**: Stored in a persistent ChromaDB collection with multi-tenant metadata indexing.
5. **Contextual Query Rewriting**: If a user submits a follow-up query with pronouns or ellipsis (e.g. *"Can you give an example of the second one?"*), the query rewriter uses conversation context to produce a self-contained search query.
6. **MMR Retrieval**: Maximal Marginal Relevance (MMR) balances relevance and diversity (`top_k=4`, `fetch_k=20`, `lambda_mult=0.7`) under multi-tenant filtering.
7. **Grounded Synthesis**: Retrieved chunks and query are injected into Gemini 2.5 Flash with strict anti-hallucination directives.
8. **Citations**: Citations link each factual statement back to specific pages or video timestamps.

---

## Tech Stack

### Backend & AI Engine
- **Language**: Python 3.11
- **API Framework**: FastAPI 0.115+
- **ASGI Server**: Uvicorn
- **ORM & Migrations**: SQLAlchemy 2.0, Alembic
- **Vector Database**: ChromaDB 0.6+
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (Hugging Face)
- **LLM Engine**: Google Gemini (`gemini-2.5-flash`) via `google-genai`
- **Authentication**: JWT (JSON Web Tokens), `passlib[bcrypt]`
- **Testing**: Pytest, Pytest-Asyncio, HTTPX

### Frontend
- **Framework**: React 19
- **Bundler & Build**: Vite 6
- **Styling**: Tailwind CSS v4
- **Routing**: React Router 7 (SPA Mode)
- **Data Fetching & State**: Axios, Custom Hooks
- **Icons**: Lucide React

---

## Repository Structure

```
StudyPilot-AI/
├── ai_engine/                         # Standalone AI/RAG Engine Package
│   ├── embeddings/                    # Local SentenceTransformer embeddings
│   ├── llm/                           # Gemini client, system prompts, query rewriters
│   ├── loaders/                       # PDF, Text, and YouTube transcript loaders
│   ├── preprocessing/                 # Text cleaning, chunking, metadata enrichment
│   ├── services/                      # Chat, Notes, Summary, Quiz services
│   ├── utils/                         # Exceptions, logging, summary cache
│   ├── vectorstore/                   # ChromaDB interface & MMR retriever
│   ├── engine.py                      # Main AIEngine facade
│   └── tests/                         # 30 automated unit tests
├── backend/                           # FastAPI REST API Application
│   ├── app/
│   │   ├── ai/                        # Singleton AIEngine provider
│   │   ├── api/                       # API routes (auth, chat, study, resources, etc.)
│   │   ├── core/                      # Configuration, security, logging
│   │   ├── db/                        # SQLAlchemy session, base, and models
│   │   ├── repositories/              # Database repository pattern layer
│   │   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── services/                  # Business logic services
│   │   └── main.py                    # FastAPI entrypoint
│   └── tests/                         # 15 automated integration tests
├── frontend/                          # React 19 Frontend Application
│   ├── public/                        # Static assets (favicons, icons)
│   ├── src/
│   │   ├── app/                       # Application routers and providers
│   │   ├── components/                # Layout, study tabs, workspace components
│   │   ├── context/                   # AuthContext, ThemeContext
│   │   ├── hooks/                     # Custom React hooks (useChat, useStudy, etc.)
│   │   ├── pages/                     # SPA views (Workspace, Resources, History, etc.)
│   │   └── services/                  # API client modules
│   ├── package.json                   # NPM dependencies and scripts
│   └── vite.config.js                 # Vite bundler configuration
├── alembic/                           # PostgreSQL database migrations
├── scripts/                           # Database seeding and E2E verification scripts
│   ├── demo_queries.sql               # Verified SQL queries for testing
│   ├── populate_synthetic_student.py  # Development database seed script
│   └── e2e_golden_test.py             # End-to-end verification suite
├── .env.example                       # Reference environment variables
├── .gitignore                         # Git exclusion rules
├── pyproject.toml                     # Python package and test configuration
└── requirements.txt                   # Production Python dependencies
```

---

## Local Development Guide

### 1. Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: v18.0 or higher (v20+ recommended)
- **PostgreSQL**: Local or remote instance running on port 5432

### 2. Backend Setup

```bash
# Clone the repository
git clone https://github.com/sanskarchourasiya445/StudyPilot-AI.git
cd StudyPilot-AI

# Create and activate Python virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and supply your GEMINI_API_KEY and PostgreSQL credentials
```

### 3. Database Initialization

```bash
# Run database migrations with Alembic
alembic upgrade head

# (Optional) Seed the database with sample demo data:
python scripts/populate_synthetic_student.py
```

### 4. Running the Backend

```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/health`

### 5. Frontend Setup

```bash
cd frontend

# Install Node dependencies
npm install

# Configure frontend environment
cp .env.example .env

# Run Vite development server
npm run dev
```
- Application Web UI: `http://localhost:5173`

---

## Environment Variables

All sensitive values must be configured via environment variables. See [`.env.example`](file:///.env.example) for reference:

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg2://user:pass@localhost:5432/studypilot` |
| `GEMINI_API_KEY` | Google AI Studio API key | `AIzaSy...` |
| `SECRET_KEY` | Secret key for signing JWT tokens | Random 32+ character hex string |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| JWT session duration | `1440` (24 hours) |
| `ALGORITHM` | JWT cryptographic algorithm | `HS256` |
| `PROJECT_NAME` | Application display name | `StudyPilot AI` |
| `BACKEND_CORS_ORIGINS` | Permitted CORS origins (JSON array) | `["http://localhost:5173","http://127.0.0.1:5173"]` |
| `CHROMA_PERSIST_DIRECTORY` | On-disk path for ChromaDB storage | `data/chroma_db` |

---

## Verification & Testing

The repository includes a comprehensive, verified test suite covering both the AI RAG Engine and the FastAPI application layer.

```bash
# Run all automated tests (45 tests total)
pytest

# Run backend API integration tests
pytest backend/tests

# Run AI Engine RAG & unit tests
pytest ai_engine/tests

# Run frontend production build check
cd frontend && npm run build
```

### Test Suite Execution Status

```
========================= 45 passed in 24.12s =========================
- backend/tests/test_adaptive_quiz.py           [PASS]
- backend/tests/test_ai_capabilities.py          [PASS]
- backend/tests/test_auth.py                     [PASS]
- backend/tests/test_config.py                   [PASS]
- backend/tests/test_conversations.py            [PASS]
- backend/tests/test_e2e_flow.py                 [PASS]
- backend/tests/test_health.py                   [PASS]
- backend/tests/test_mastery.py                  [PASS]
- backend/tests/test_multi_resource_scope.py     [PASS]
- backend/tests/test_resources.py                [PASS]
- backend/tests/test_revision.py                 [PASS]
- ai_engine/tests/test_chat.py                   [PASS]
- ai_engine/tests/test_chat_contextual.py        [PASS]
- ai_engine/tests/test_pdf.py                    [PASS]
- ai_engine/tests/test_summary_cache.py          [PASS]
- ai_engine/tests/test_youtube.py                [PASS]
```

---

---

## Production Deployment Guide (Render Native + Neon)

StudyPilot AI is configured for deployment as a **Render Native Web Service** (Python runtime) backed by **Neon Serverless PostgreSQL** and Google Gemini 2.5 Flash. Docker is not required for this deployment.

### Architecture in Production

```
┌────────────────────────────────────────────────────────┐
│               Render Native Web Service                │
│                                                        │
│  FastAPI ASGI Server (0.0.0.0:$PORT)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  FastAPI Application (Uvicorn)                   │  │
│  │  ├── Serves Production Frontend (Vite static)    │  │
│  │  ├── REST API (/api/*)                           │  │
│  │  └── Embedded AI Engine (all-MiniLM-L6-v2)       │  │
│  └──────────────────────────────────────────────────┘  │
│                            │                           │
│  Persistent Mount: /data   │                           │
│  ├── /data/chroma_db       │ (Vectors & Chunks)        │
│  └── /data/uploads         │ (Ingested PDFs)           │
└──────────────┬─────────────────────────────┬───────────┘
               │                             │
               ▼                             ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐
│   Neon Managed PostgreSQL    │ │    Google Gemini 2.5 API     │
│   (Serverless, SSL pooled)   │ │    (gemini-2.5-flash)        │
└──────────────────────────────┘ └──────────────────────────────┘
```

### 1. Free vs. Paid Render Plan Breakdown

| Feature | Render Free Web Service | Render Paid Web Service (with Persistent Disk) |
| :--- | :--- | :--- |
| **Relational Data (PostgreSQL)** | Fully persistent in external Neon DB | Fully persistent in external Neon DB |
| **Vector DB (ChromaDB)** | **Ephemeral**: embeddings reset when service sleeps/redeploys | **Durable**: stored on persistent disk (`/data/chroma_db`) |
| **PDF Uploads** | **Ephemeral**: uploaded files reset on sleep/redeploy | **Durable**: stored on persistent disk (`/data/uploads`) |
| **Sleep / Spin-down** | Spins down after 15 minutes of inactivity | Never sleeps; always responsive |
| **Recommendation** | Suitable for testing and demos | **Required for full persistence** |

---

### 2. Step-by-Step Render Deployment

#### Step A: Set up Managed PostgreSQL on Neon
1. Create a free project at [neon.tech](https://neon.tech).
2. Under **Dashboard > Connection Details**, copy the connection string.
   - Choose **Connection pooling** (`postgresql://user:pass@ep-xyz-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require`).
   - The application automatically normalizes `postgresql://` $\rightarrow$ `postgresql+psycopg2://` and configures connection pre-pinging with short recycling pools (`pool_recycle=300`) suitable for Neon serverless architecture.

#### Step B: Create a Render Native Web Service
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** $\rightarrow$ **Web Service**.
3. Connect your GitHub repository: `sanskarchourasiya445/StudyPilot-AI`.
4. Configure service settings:
   - **Name**: `studypilot-ai`
   - **Region**: Choose the region closest to your Neon database (e.g., Oregon or Ohio).
   - **Runtime**: **Python**.
   - **Build Command**:
     ```bash
     cd frontend && npm install && npm run build && cd .. && pip install -r requirements.txt
     ```
   - **Pre-Deploy Command** (under Advanced):
     ```bash
     alembic upgrade head
     ```
   - **Start Command**:
     ```bash
     uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Health Check Path**: `/health`
   - **Instance Type / Plan**:
     - Select a paid plan (e.g. Starter) if you are attaching a persistent disk for durable ChromaDB/uploads.
     - Select **Free** if testing without persistent disk.

#### Step C: Attach Persistent Disk (For Paid Plans)
If you are deploying on a paid plan with persistent disk:
1. Under **Disks** $\rightarrow$ Click **Add Disk**.
2. **Name**: `studypilot-data`
3. **Mount Path**: `/data`
4. **Size**: `10 GB` (or desired size)

#### Step D: Configure Environment Variables
Under **Environment Variables**, add the following:

**Required Secrets:**
| Key | Value Description |
| :--- | :--- |
| `DATABASE_URL` | Neon PostgreSQL pooled connection string with SSL (`sslmode=require`) |
| `GEMINI_API_KEY` | Google AI Studio API key |
| `JWT_SECRET` (or `SECRET_KEY`) | Secure 32+ character random hex string (`python -c "import secrets; print(secrets.token_hex(32))"`) |

**Configuration Variables:**
| Key | Default / Value | Description |
| :--- | :--- | :--- |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Production Gemini LLM model |
| `CHROMA_PERSIST_DIRECTORY` | `/data/chroma_db` | Vector store directory (falls back to local `data/chroma_db` if disk unattached) |
| `UPLOAD_DIR` | `/data/uploads` | PDF storage directory (falls back to local `data/uploads` if disk unattached) |
| `MAX_UPLOAD_SIZE_MB` | `50` | Maximum file upload size limit |

#### Step E: Deploy
1. Click **Create Web Service**.
2. Render executes the build command: builds the React frontend with Vite and installs Python dependencies.
3. Render runs `alembic upgrade head` before start.
4. Uvicorn starts on `0.0.0.0:$PORT` serving both the SPA frontend and `/api` backend.
5. Your application is live at `https://<service-name>.onrender.com`.

---

### 3. Local Production Simulation (Without Docker)

You can simulate the production runtime locally using Uvicorn:

```bash
# 1. Build the production frontend
cd frontend && npm install && npm run build && cd ..

# 2. Run database migrations
alembic upgrade head

# 3. Start the application with Render-style start command
uvicorn backend.app.main:app --host 0.0.0.0 --port 10000
```

Access the application in your browser at `http://localhost:10000` or test health at `http://localhost:10000/health`.

---

## Known Limitations

- **Render Free Ephemeral Storage**: If deployed on the Render Free plan without a persistent disk, uploaded PDF files and local ChromaDB embeddings are ephemeral and will be wiped when the service spins down or restarts. Relational user data, conversations, notes, summaries, and quizzes in Neon PostgreSQL remain fully intact.
- **YouTube Transcript Dependency**: YouTube ingestion relies on public captions or subtitles via `youtube-transcript-api`. Videos with disabled captions require the local Whisper fallback.
- **External LLM Quota**: Generation speed and availability are subject to Google Gemini API quotas and rate limits.

---

## Security

- **Authentication**: Stateless JWT bearer tokens with standard SHA-256 HMAC signatures.
- **Password Security**: Passwords hashed using `bcrypt` via `passlib`.
- **Multi-Tenant Scoping**: All vector queries and SQL transactions enforce `user_id` filtering at the repository and retriever layers to prevent cross-account data leakage.
- **Strict Parameter Validation**: All incoming requests validated using Pydantic v2 schemas.
- **Same-Origin Production**: Frontend and backend are served from the same origin on Render, eliminating cross-origin CORS exposure.

---

## Roadmap

- [x] Render Native Python Web Service deployment configuration (`render.yaml`).
- [x] Neon serverless PostgreSQL connection pooling and auto-migrations.
- [x] Unified single-origin SPA serving with FastAPI.
- [ ] Docker containerization as an optional alternative deployment target.
- [ ] Asynchronous background job queue (Celery/ARQ) for heavy multi-document ingestion.
- [ ] Export study notes to Markdown, PDF, and Anki flashcard format.



---

## License

This project is licensed under the [MIT License](LICENSE).
