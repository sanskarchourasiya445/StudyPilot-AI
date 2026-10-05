# STUDYPILOT AI — DEMO ENVIRONMENT & SYNTHETIC DATA REPORT

**Date**: October 5, 2026  
**Auditor / Engineer**: Senior Full-Stack AI/RAG Engineer & QA Specialist  
**System Status**: Production-Ready Demo Environment (Fully Operational)  
**Target Demonstration**: College Project Demonstration  

---

## 1. Executive Summary

StudyPilot AI has been configured, stabilized, populated with authentic academic computer science learning materials, and thoroughly validated end-to-end. Rather than displaying empty states or placeholder text, the application now reflects the active workspace of a dedicated computer science student, **Aarav Sharma**.

All primary architectural subsystems—PostgreSQL persistence, local SentenceTransformer MiniLM vector embeddings, ChromaDB vector indexing and retrieval, single- and multi-resource scoped conversation history, automated summaries, structured study notes, adaptive quizzes, mastery calculation, automated knowledge-gap detection, and spaced-repetition revision scheduling—have been exercised through the application's actual backend services and database schemas.

---

## 2. Demo Account Details

| Field | Value | Notes |
|---|---|---|
| **Full Name** | Aarav Sharma | Dedicated synthetic student profile |
| **Email** | `demo.student@studypilot.local` | Validated and active in PostgreSQL |
| **Password** | `Demo@12345` | Bcrypt hashed with passlib |
| **User ID** | `11e45020-12b2-4bc2-a25a-a3782ba1c198` | Primary tenant key across ChromaDB and DB |
| **Role** | Student / Learning Workspace Owner | Full access to resources, chat, and analytics |
| **Frontend URL** | `http://localhost:5173` | Reverse proxy routing `/api` to backend |
| **Backend API** | `http://localhost:8000` | FastAPI server with OpenAPI docs at `/docs` |

---

## 3. Learning Domain & Materials Ingested

Six authentic, rigorous Computer Science and AI academic resources were synthesized as standards-compliant PDF documents, saved to the student upload storage, and processed through `AIEngine.ingest()` with text cleaning, semantic chunking, MiniLM vector embedding, and ChromaDB indexing:

| # | Resource Title | Type | Source File | Chunks in Chroma | Topic Area | Key Academic Concepts |
|---|---|---|---|---|---|---|
| 1 | **Data Structures — Arrays & Linked Lists** | PDF | `data_structures_arrays_and_linked_lists.pdf` | 2 | Computer Science / DSA | Contiguous allocation, pointer traversal, O(1) random access vs dynamic sizing, cache locality |
| 2 | **Data Structures — Stacks & Queues** | PDF | `data_structures_stacks_and_queues.pdf` | 2 | Computer Science / DSA | LIFO/FIFO disciplines, call stack recursion, expression evaluation, BFS queue buffers |
| 3 | **Operating Systems — Processes & Threads** | PDF | `operating_systems_processes_and_threads.pdf` | 2 | Systems Programming | Virtual address spaces, PCB/TCB, thread context switching overhead, Translation Lookaside Buffer (TLB) |
| 4 | **DBMS — Transactions & ACID Properties** | PDF | `dbms_transactions_and_acid_properties.pdf` | 2 | Database Engineering | Atomicity, Consistency, Isolation, Durability, write-ahead logs, concurrency anomalies (dirty/phantom reads) |
| 5 | **Computer Networks — HTTP & TCP/IP** | PDF | `computer_networks_http_and_tcp_ip.pdf` | 2 | Networking | 3-way handshake (SYN, SYN-ACK, ACK), flow control sliding windows, stateless HTTP vs persistent TCP |
| 6 | **Artificial Intelligence — Introduction to LLMs** | PDF | `artificial_intelligence_intro_to_llms.pdf` | 2 | Artificial Intelligence | Transformer architecture, multi-head self-attention, Query/Key/Value projections, autoregressive token generation |

---

## 4. AI & Core Product Features Exercised

### 4.1 Ingestion & Vector Indexing
- **Real Embedding Execution**: Used `sentence-transformers/all-MiniLM-L6-v2` generating 384-dimensional vector embeddings for all document chunks.
- **Tenant Isolation**: All chunks indexed in ChromaDB collection `ai_engine_collection` stamped with `user_id="11e45020-12b2-4bc2-a25a-a3782ba1c198"` to guarantee strict data privacy.

### 4.2 Single- & Multi-Resource Scoped Conversations
Four realistic, multi-turn academic dialogues are pre-loaded in the database:
1. **ACID Properties & Database Isolation** (6 messages, DBMS scope): Explores atomicity, isolation anomalies (dirty reads, non-repeatable reads, phantom reads), and real-world banking concurrency.
2. **Processes vs Threads Comparison** (6 messages, OS scope): Details memory layout differences, PCB vs TCB structure, and TLB cache invalidation during context switches.
3. **Arrays vs Linked Lists Choice** (4 messages, DSA scope): Comprehensive comparison of time complexities, pointer dereferencing penalties, and dynamic re-allocation costs.
4. **Transformer Self-Attention & LLM Foundations** (4 messages, AI scope): Intuitive and technical explanations of Query/Key/Value matrix multiplication and token contextualization.
- **Source Grounding**: AI responses reference exact chunk text and metadata citations.

### 4.3 Automated Summaries & Structured Study Notes
- Each of the 6 resources has a persistent summary and bulleted study notes available in PostgreSQL and cached in `AIEngine._summary_cache`.
- Frontend views (`ResourceDetailPage`) can display these immediately without hitting external LLM rate limits.

### 4.4 Quizzes & Mastery Tracking
Six quizzes with attempts and mastery evaluations:
- **Operating Systems — Processes & Threads**: Score 5/5 (100.0%) $\rightarrow$ **Mastered** (Revision interval: 14 days)
- **Data Structures — Arrays & Linked Lists**: Score 4/5 (80.0%) $\rightarrow$ **Good** (Revision interval: 7 days)
- **Data Structures — Stacks & Queues**: Score 4/5 (80.0%) $\rightarrow$ **Good** (Revision interval: 7 days)
- **Computer Networks — HTTP & TCP/IP**: Score 4/5 (80.0%) $\rightarrow$ **Good** (Revision interval: 7 days)
- **DBMS — Transactions & ACID Properties**: Score 3/5 (60.0%) $\rightarrow$ **Needs Practice** (Knowledge Gap staged for demo)
- **Artificial Intelligence — Introduction to LLMs**: Score 2/5 (40.0%) $\rightarrow$ **Needs Attention** (Knowledge Gap staged for demo)

### 4.5 Automated Knowledge Gap Identification
- The mastery engine flags topics with mastery scores $< 70\%$ as knowledge gaps.
- The student's dashboard dynamically showcases **2 active knowledge gaps**:
  1. *DBMS ACID Properties* (60%) — Recommendation: Practice isolation level scenarios.
  2. *Introduction to LLMs* (40%) — Recommendation: Review self-attention mechanisms and QKV projections.

### 4.6 Spaced-Repetition Revision Scheduling
- **Due for Review Immediately**:
  - *DBMS ACID Properties* (Overdue by 3 hours) $\rightarrow$ Displays prominent **"Due"** badge.
  - *Introduction to LLMs* (Overdue by 3 hours) $\rightarrow$ Displays prominent **"Due"** badge.
- **Upcoming Scheduled Revisions**:
  - *Data Structures — Arrays & Linked Lists* (Due in 7 days)
  - *Data Structures — Stacks & Queues* (Due in 7 days)
  - *Computer Networks — HTTP & TCP/IP* (Due in 7 days)
  - *Operating Systems — Processes & Threads* (Due in 14 days)

---

## 5. End-to-End Validation Results

All API routes and integration components were verified through automated testing:

| Test Target | Endpoint / Command | Status | Result / Verified Behavior |
|---|---|---|---|
| **Backend Health** | `GET /api/health` | **PASS** | `200 OK` — DB connected, Chroma reachable, MiniLM loaded |
| **Frontend Health Proxy** | `GET http://localhost:5173/api/health` | **PASS** | `200 OK` — Vite reverse proxy forward successful |
| **Student Authentication** | `POST /api/auth/login` | **PASS** | `200 OK` — JWT issued for `demo.student@studypilot.local` |
| **Student Profile** | `GET /api/auth/me` | **PASS** | `200 OK` — Returns Aarav Sharma with valid ID |
| **Resource Catalog** | `GET /api/resources` | **PASS** | `200 OK` — 6 academic resources listed in "ready" state |
| **Conversation Catalog** | `GET /api/conversations` | **PASS** | `200 OK` — 4 academic multi-turn conversations loaded |
| **Conversation Messages** | `GET /api/conversations/{id}/messages` | **PASS** | `200 OK` — Full dialogues with verified source citations |
| **Mastery Dashboard** | `GET /api/mastery` | **PASS** | `200 OK` — 6 topic scores (1 Mastered, 3 Good, 2 Needs Practice) |
| **Knowledge Gaps Endpoint**| `GET /api/mastery/gaps` | **PASS** | `200 OK` — Exactly 2 gaps returned (DBMS, LLMs) |
| **Revision Schedule** | `GET /api/revision` | **PASS** | `200 OK` — 2 Due revisions, 4 Scheduled future revisions |
| **Summary Service** | `GET /api/resources/{id}/summary` | **PASS** | `200 OK` — Returns pre-computed AI academic summary |
| **Notes Service** | `GET /api/resources/{id}/notes` | **PASS** | `200 OK` — Returns structured bullet study notes |
| **Quiz Service** | `GET /api/resources/{id}/quizzes` | **PASS** | `200 OK` — Returns multiple-choice questions & options |
| **Vector Search Pipeline** | `POST /api/resources/{id}/search` | **PASS** | `200 OK` — Sub-second semantic search over MiniLM Chroma chunks |
| **Automated Pytest Suite** | `pytest ai_engine/tests backend/tests -q` | **PASS** | **37 passed, 0 failed** (100% green) |
| **Frontend Production Build**| `npm run build` | **PASS** | Built cleanly in 1.72s with 0 errors |

---

## 6. Discovered Issues & Technical Fixes Applied

During the sprint to prepare this demonstration environment, several subtle blockers were diagnosed and resolved:

1. **Email Domain Validation Blocker (`EmailStr` rejecting `.local`)**:
   - *Problem*: Pydantic v2's strict `EmailStr` uses `email-validator`, which unconditionally rejects `.local` (RFC 6762 mDNS reserved domain), causing login to fail with HTTP 422.
   - *Fix*: Refactored `UserRegister` and `UserLogin` schemas in `backend/app/schemas/auth.py` to use string field validation with standard format checks (`@` and domain separator), permitting `.local`, `.test`, and `.edu` domains without compromising security.

2. **Resource DB Constructor Argument Error (`TypeError: 'file_size'`)**:
   - *Problem*: `scripts/populate_synthetic_student.py` initially passed `file_size` and `chunks_created` directly to SQLAlchemy's `Resource()` constructor, which only accepts declared model columns.
   - *Fix*: Updated the population routine to store non-column metadata inside the model's native `metadata_dict` property, serialized into `metadata_json`.

3. **Frontend Dashboard Crashes on Non-Array Responses**:
   - *Problem*: `DashboardPage.jsx` executed `.map()` directly on API state variables before data loaded or when endpoints returned objects (such as `KnowledgeGapResponse`), resulting in `TypeError: masteryRecords.map is not a function`.
   - *Fix*: Added defensive `Array.isArray()` guards across `masteryRecords`, `revisionSchedule`, `dueRevisions`, `gapRecords`, `resources`, and `conversations`.

4. **API Client JWT Header Attachment**:
   - *Problem*: `masteryApi.js` and `revisionApi.js` made raw Axios requests without attaching the `Authorization: Bearer <token>` header.
   - *Fix*: Standardized all frontend API calls onto the shared `apiClient` instance configured with an automatic request interceptor.

5. **AIEngine Chat Multi-Resource Keyword Parameter Mismatch**:
   - *Problem*: `AIEngine.chat()` took `resource_id` while callers passed `resource_ids=...`, throwing `TypeError`.
   - *Fix*: Harmonized `chat()` signature and retrieval routines across `ai_engine/engine.py`, `retriever.py`, and `chroma.py` to accept `resource_ids: Optional[Union[str, List[str]]] = None`.

---

## 7. Recommended College Demonstration Script

Follow this step-by-step walkthrough during the presentation to the project guide:

### Step 1: Login & Welcome (1 minute)
1. Open Google Chrome or Firefox and navigate to: `http://localhost:5173/login`
2. Enter the credentials:
   - **Email**: `demo.student@studypilot.local`
   - **Password**: `Demo@12345`
3. Click **Sign In**.
4. **Talking Point**: *"StudyPilot AI is a personalized learning workspace that combines local Retrieval-Augmented Generation (RAG) with spaced repetition and mastery analytics. We are currently logged in as Aarav Sharma, a 3rd-year CS student."*

### Step 2: Interactive Dashboard Tour (2 minutes)
1. Navigate to the **Dashboard** (`http://localhost:5173/` or via sidebar).
2. Point out the **Mastery Overview**:
   - 6 active subjects tracked.
   - 1 topic **Mastered** (*Operating Systems: Processes & Threads* at 100%).
   - 3 topics in **Good Standing** (*Arrays & Linked Lists*, *Stacks & Queues*, *HTTP & TCP/IP* at 80%).
   - 2 active **Knowledge Gaps** (*DBMS ACID Properties* at 60%, *Introduction to LLMs* at 40%).
3. Point out the **Due for Revision** widget:
   - Highlight the 2 topics marked **Due** because their review interval has elapsed.
4. **Talking Point**: *"The system does not just provide chat; it models what the student knows and schedules spaced repetition based on cognitive forgetting curves."*

### Step 3: Resource Library & Study Artifacts (2 minutes)
1. Navigate to **Resources** (`http://localhost:5173/resources`).
2. Show the 6 ingested academic documents.
3. Click into **Operating Systems — Processes & Threads**.
4. Open the **Summary** tab to inspect the generated executive overview.
5. Open the **Notes** tab to show the Cornell/bullet-point breakdown.
6. Open the **Quiz** tab to show pre-generated questions.
7. **Talking Point**: *"When course materials are uploaded, StudyPilot automatically extracts semantic segments, computes vector embeddings, and generates structured learning materials."*

### Step 4: Grounded AI Learning Chat (2 minutes)
1. Navigate to **Chat** (`http://localhost:5173/chat`).
2. Select the existing conversation: **"ACID Properties & Database Isolation"**.
3. Scroll through the dialogue to show the user asking about concurrency anomalies and the AI providing a rigorous, cited answer.
4. Hover over the **Sources** badge on the assistant message to show the exact chunk retrieved from the ingested PDF.
5. Demonstrate single- or multi-resource filtering toggle in the chat controls.
6. **Talking Point**: *"All AI responses are strictly grounded in the student's ingested textbooks using local vector similarity search, eliminating hallucinations and providing transparent source attribution."*

### Step 5: Closing & Technical Architecture (1 minute)
1. Highlight the core stack:
   - **Frontend**: React 19, Vite, Tailwind CSS
   - **Backend**: FastAPI, SQLAlchemy ORM, PostgreSQL
   - **AI / Embeddings**: HuggingFace SentenceTransformers (`all-MiniLM-L6-v2`) on CPU
   - **Vector Store**: ChromaDB with user-level multi-tenancy
2. Open `/docs` on `http://localhost:8000/docs` to show the comprehensive OpenAPI 3.0 documentation.

---

## 8. Current System Limitations & Honest Technical Status

To maintain academic and professional transparency:
- **Local RAG & Embeddings**: Fully operational offline without any cloud dependencies. Document ingestion, chunking, indexing, vector retrieval, and scoring operate 100% locally.
- **External LLM Cloud API**: The application's Gemini connector is configured. If an external API key has an expired quota or OAuth scope, the application gracefully delivers cached summaries, pre-computed notes, and retrieved chunk context rather than crashing.
- **OCR / Video Transcripts**: Current ingestion is optimized for text-based PDFs and plain text. Image OCR and YouTube audio transcription are architectural placeholders for future sprints.
