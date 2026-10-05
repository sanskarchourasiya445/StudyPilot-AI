# StudyPilot Frontend Implementation Specification

## 1. Purpose

Build the complete frontend for **StudyPilot**, an AI-powered study assistant that lets students ingest PDFs and YouTube lectures, chat with their study material, generate summaries and notes, and practice with AI-generated quizzes.

The existing StudyPilot AI Engine and FastAPI backend are the source of truth for application behavior. The frontend must consume the backend APIs and must not reimplement AI, retrieval, database, authentication, or business logic.

The goal is a production-minded, responsive, accessible React application with a clean student-focused UI and a strong light/dark theme system.

---

# 2. Technology Stack

Use exactly this frontend stack unless a real technical reason requires a change:

* **React**
* **JavaScript** — do NOT use TypeScript for this project
* **Vite**
* **Tailwind CSS**
* **React Router**
* **TanStack Query** for server state, caching, loading/error states, and API synchronization
* **Axios** for HTTP communication
* **React Hook Form** for forms where useful
* **Zod** for client-side schema validation where useful
* **Lucide React** for icons

Do not introduce a large UI component framework unless necessary. Prefer reusable local components built with Tailwind.

---

# 3. Visual Design Direction

The provided StudyPilot UI references establish the visual direction.

Do NOT make the application predominantly purple.

Use a **primary-color driven interface** with a clean white/light-gray base and strong semantic accents:

* Primary blue for main actions, active navigation, links, and focus states
* Green for success, ready states, completed study actions, and positive feedback
* Orange/yellow for study actions, quiz emphasis, processing states, and attention cues
* Red for destructive actions, failures, and YouTube/error states where appropriate
* Teal/cyan for secondary AI/system states
* Purple only as a restrained secondary accent, not the dominant brand color
* Dark navy/slate for text and dark-mode surfaces

The interface should feel:

* modern
* academic
* focused
* trustworthy
* calm
* lightweight
* professional
* responsive

Avoid excessive gradients, excessive glassmorphism, neon colors, giant decorative illustrations, and unnecessary animation.

Use:

* rounded cards
* subtle shadows
* strong whitespace
* clear typography hierarchy
* compact but comfortable spacing
* clear primary actions
* consistent iconography

---

# 4. Theme System

Implement a complete **Light / Dark mode** system.

Requirements:

* Theme toggle available from the global UI/settings
* Support `light`, `dark`, and optionally `system` preference
* Persist the user's selected theme in `localStorage`
* Apply the theme before the application renders when possible to avoid a flash of the wrong theme
* All components must work in both themes
* Do not hard-code colors that break in dark mode
* Use semantic Tailwind theme classes/variables consistently

Suggested theme tokens:

```text
background
surface
surface-muted
border
text-primary
text-secondary
primary
success
warning
error
info
```

Light mode should use a white/off-white background with slate text and strong blue primary actions.

Dark mode should use deep navy/slate surfaces, light text, muted borders, and the same semantic primary colors with adjusted contrast.

---

# 5. Application Architecture

Use a feature-oriented modular React structure.

Recommended structure:

```text
frontend/
├── src/
│   ├── app/
│   │   ├── App.jsx
│   │   ├── router.jsx
│   │   ├── providers.jsx
│   │   └── queryClient.js
│   │
│   ├── assets/
│   │
│   ├── components/
│   │   ├── ui/
│   │   ├── layout/
│   │   ├── navigation/
│   │   ├── feedback/
│   │   └── common/
│   │
│   ├── features/
│   │   ├── auth/
│   │   ├── resources/
│   │   ├── chat/
│   │   ├── summaries/
│   │   ├── notes/
│   │   ├── quizzes/
│   │   ├── conversations/
│   │   ├── search/
│   │   └── settings/
│   │
│   ├── layouts/
│   │   ├── AppLayout.jsx
│   │   ├── AuthLayout.jsx
│   │   └── StudyLayout.jsx
│   │
│   ├── pages/
│   │   ├── DashboardPage.jsx
│   │   ├── ResourcesPage.jsx
│   │   ├── ResourceDetailPage.jsx
│   │   ├── StudyWorkspacePage.jsx
│   │   ├── SummariesPage.jsx
│   │   ├── NotesPage.jsx
│   │   ├── QuizPage.jsx
│   │   ├── ConversationsPage.jsx
│   │   ├── ConversationDetailPage.jsx
│   │   ├── SearchPage.jsx
│   │   ├── SettingsPage.jsx
│   │   ├── LoginPage.jsx
│   │   ├── RegisterPage.jsx
│   │   ├── NotFoundPage.jsx
│   │   └── ErrorPage.jsx
│   │
│   ├── services/
│   │   ├── apiClient.js
│   │   ├── authApi.js
│   │   ├── resourceApi.js
│   │   ├── chatApi.js
│   │   ├── studyApi.js
│   │   └── conversationApi.js
│   │
│   ├── hooks/
│   │   ├── useAuth.js
│   │   ├── useTheme.js
│   │   ├── useResources.js
│   │   ├── useChat.js
│   │   └── useConversations.js
│   │
│   ├── context/
│   │   ├── AuthContext.jsx
│   │   └── ThemeContext.jsx
│   │
│   ├── utils/
│   ├── constants/
│   └── main.jsx
│
├── public/
├── .env.example
├── package.json
├── vite.config.js
├── tailwind.config.js
└── README.md
```

The exact grouping may be simplified where appropriate, but maintain clear separation between pages, reusable UI, API services, and feature logic.

---

# 6. Core Principle: Backend Is the Source of Truth

The frontend communicates with the existing FastAPI backend.

Do NOT:

* call Gemini directly from React
* access Chroma directly
* access PostgreSQL directly
* duplicate authentication logic
* implement RAG retrieval in the frontend
* reimplement summary/notes/quiz generation
* duplicate backend business rules

The flow must be:

```text
React UI
   ↓
API service
   ↓
FastAPI backend
   ↓
AI Engine / PostgreSQL
```

---

# 7. API Integration

Use a single configured Axios client.

Example responsibilities:

```text
apiClient
├── base URL from VITE_API_BASE_URL
├── JSON defaults
├── auth token handling
├── centralized error normalization
└── optional request cancellation
```

Keep API logic out of page components.

Use TanStack Query for server state.

Examples of server state:

* current user
* resources
* resource details
* conversations
* messages
* summaries
* notes
* quizzes
* search results

Do not store server data in local React state unless it is temporary UI state.

---

# 8. Authentication Flow

Implement:

```text
Login
Register
Logout
Current user
Protected routes
```

Use the backend authentication system as the source of truth.

Requirements:

* login form
* registration form
* authentication loading state
* invalid credentials handling
* session restoration
* protected route guard
* redirect unauthenticated users to login
* redirect authenticated users away from login/register where appropriate
* logout and clear client auth state

Never store passwords.

Never log auth tokens.

Use secure token handling consistent with the backend's authentication contract.

---

# 9. Global Application Layout

Authenticated layout should contain:

### Sidebar

* StudyPilot logo/brand
* Dashboard
* Resources
* Conversations
* Summaries
* Notes
* Quizzes
* Search
* Settings
* Logout
* user profile area
* optional storage/status indicator

### Top bar

* breadcrumbs/page title where useful
* global search
* theme toggle
* notification/status area if supported
* profile menu

### Responsive behavior

Desktop:

* persistent sidebar

Tablet:

* collapsible sidebar

Mobile:

* drawer/navigation sheet
* no permanently visible large sidebar

---

# 10. Page Requirements

## Dashboard

Purpose: give the student an overview and a fast entry into studying.

Include:

* welcome message
* upload resource CTA
* add YouTube CTA
* resource count
* conversation count
* summary count
* quiz count
* recent resources
* continue studying
* recent conversations
* quick actions

Quick actions:

* Start new chat
* Add PDF
* Add YouTube
* Generate summary
* Take quiz
* Write/view notes

---

## Resources

Show all user resources.

Features:

* search
* filtering by type
* filtering by status
* sorting
* pagination if provided by backend
* resource cards/table
* PDF and YouTube visual distinction
* processing states
* ready state
* failed state
* resource actions
* delete confirmation

Resource row/card should show:

* title/source
* type
* status
* date added
* chunk/metadata information when available
* actions

---

## Resource Detail

Show a selected PDF or YouTube resource.

Include:

* title
* source information
* resource type
* status
* metadata
* created/updated information
* summary status
* actions

Primary actions:

* Start Chat
* Generate/View Summary
* Generate/View Notes
* Take Quiz
* Search resource
* Delete resource

For YouTube resources, show a clear YouTube identity and source link when returned by the backend.

---

# 11. Study Workspace / Chat

This is the core StudyPilot experience.

Layout:

```text
┌──────────────┬─────────────────────────┬──────────────────────┐
│ conversation │ chat messages           │ source citations      │
│ history      │                         │ / context panel       │
│              │                         │                       │
└──────────────┴─────────────────────────┴──────────────────────┘
```

Features:

* conversation history
* selected resource indicator
* user messages
* assistant messages
* loading state
* streaming-ready UI architecture if backend later supports streaming
* grounded/source citations
* source/page links where provided
* copy answer
* feedback actions
* regenerate response where supported
* message composer
* keyboard-friendly send behavior

Suggested prompts:

* Explain this topic simply
* Give me the key concepts
* What should I memorize?
* Compare these concepts
* Make a quick revision plan

Never fake AI responses in production UI.

---

# 12. Summary Page

Display:

* generated summary
* generation timestamp
* cached/ready status where backend exposes it
* resource context
* regenerate action
* copy action

Important UX:

Normal "View Summary" should not create another generation request.

The UI should distinguish:

```text
Already generated → View instantly
Not generated → Generate
Regenerate → Explicitly generate fresh
```

---

# 13. Notes Page

Provide a strong reading/revision layout.

Support the styles exposed by the backend/AI Engine.

Include:

* note title
* note style
* formatted sections
* bullet points
* key takeaways
* resource reference
* copy/export-ready UI
* regenerate when appropriate

Do not build a heavy rich-text editor unless the backend requirements actually require editing notes.

---

# 14. Quiz Page

Quiz experience should feel like an actual study product, not raw JSON output.

Include:

* quiz title
* resource
* question progress
* progress bar
* question
* answer options
* selected state
* next/previous
* submit
* score screen
* correct/incorrect feedback
* explanation
* retry quiz
* difficulty/question count information

Important:

**Do not reveal the correct answer before the user submits the question.**

This is a student-facing feature.

---

# 15. Conversations

List conversations with:

* title
* resource/source when applicable
* message count
* updated time
* actions

Conversation detail should show:

* message history
* resource association
* continue chat
* delete conversation

---

# 16. Search

Global search should search the backend's supported search scope.

Show categorized results where appropriate:

* resources
* conversations
* notes
* summaries

Each result should include:

* title
* type
* relevant excerpt
* date
* navigation action

Do not perform vector retrieval from the frontend.

---

# 17. Settings

Sections:

### Profile

* name
* email
* profile information

### Appearance

* light
* dark
* optional system

### Account

* logout
* password change if backend supports it

### Preferences

* study preferences where the backend eventually supports them

Keep settings organized instead of one giant form.

---

# 18. Login / Register

Design should feel part of the same StudyPilot brand.

Login:

* email
* password
* remember/session behavior if backend supports it
* forgot password placeholder only if backend supports it
* submit
* loading state
* error state
* registration link

Register:

* name
* email
* password
* confirm password
* validation
* submit
* login link

Use a simple academic visual identity instead of a generic SaaS gradient hero.

---

# 19. Reusable Components

Create reusable UI components rather than duplicating markup.

Examples:

```text
Button
IconButton
Input
Textarea
Select
Modal
ConfirmDialog
Tabs
Badge
Card
Dropdown
Toast
Tooltip
Skeleton
EmptyState
ErrorState
LoadingState
Pagination
SearchInput
ResourceCard
ResourceTable
ResourceStatusBadge
ChatMessage
SourceCitation
SummaryCard
NotesCard
QuizQuestion
ProgressBar
Avatar
Sidebar
Topbar
```

Components should support both themes.

---

# 20. Loading, Empty, and Error States

Every major data-driven page needs all three.

### Loading

Use skeletons or purposeful loading states.

### Empty

Explain what the user should do next.

Example:

```text
No resources yet.
Upload a PDF or add a YouTube lecture to start studying.
```

### Error

Show a helpful message and a retry action when possible.

Do not show raw backend stack traces or raw Axios errors.

---

# 21. API Error UX

Normalize backend errors into user-friendly UI messages.

Examples:

```text
401 → Please log in again.
403 → You don't have access to this resource.
404 → Resource not found.
422 → Check the information you entered.
429 → AI generation is temporarily rate-limited. Try again later.
503 → AI service is temporarily unavailable.
500 → Something went wrong. Please try again.
```

Do not expose API keys, server paths, or stack traces.

---

# 22. Responsive Design

Every major page must work on:

* desktop
* laptop
* tablet
* mobile

Do not simply shrink the desktop layout.

Examples:

Chat on mobile:

* source panel becomes a drawer
* sidebar becomes a menu
* message composer remains accessible

Resources on mobile:

* switch table to cards/list

Quiz on mobile:

* one question per screen

---

# 23. Accessibility

Implement:

* semantic HTML
* keyboard navigation
* visible focus states
* sufficient color contrast
* accessible labels
* button titles where icon-only controls are used
* proper dialog semantics
* `aria-*` where required

Do not communicate meaning through color alone.

---

# 24. Motion and Interaction

Use subtle transitions only.

Good:

* sidebar transitions
* modal transitions
* hover/focus states
* skeleton shimmer
* toast entrance/exit
* tab transitions

Avoid:

* constant floating animations
* excessive parallax
* distracting page transitions
* animations that delay core actions

Respect reduced-motion preferences where possible.

---

# 25. State Management Rules

Use:

### React local state

For:

* modal open/close
* input values
* selected tab
* temporary UI state

### TanStack Query

For:

* API/server data
* resources
* conversations
* summaries
* notes
* quizzes
* user data

### Context

Only for genuinely global concerns such as:

* authentication state
* theme state

Do not introduce Redux unless the application's actual complexity proves it necessary.

---

# 26. Performance

Implement sensible performance practices:

* lazy-load large routes where appropriate
* avoid unnecessary global state
* avoid unnecessary re-renders
* use TanStack Query caching
* paginate large resource/conversation lists
* debounce search inputs where appropriate
* cancel stale requests where useful
* optimize large chat histories

Do not prematurely optimize everything.

---

# 27. Environment Variables

Create `.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

Never hardcode production API URLs into source code.

Never put Gemini/OpenAI/etc. secrets in frontend environment variables.

The frontend only needs access to the backend.

---

# 28. Testing

Use the appropriate testing strategy for the selected React setup.

At minimum test:

### Component behavior

* forms
* dialogs
* quiz interaction
* theme switching

### Page behavior

* loading states
* error states
* empty states
* protected navigation

### API integration behavior

Mock backend calls.

Do not call the real Gemini API from frontend tests.

### Critical flows

Test:

```text
Login
→ Dashboard
→ Add resource
→ Resource detail
→ Chat
→ Summary
→ Notes
→ Quiz
→ Conversations
→ Logout
```

---

# 29. Frontend Definition of Done

The frontend is complete when:

* all specified pages exist
* routing works
* authentication flow works against the backend
* resources can be added/listed/viewed/deleted through APIs
* chat works against the backend
* source citations render correctly
* summaries work
* notes work
* quizzes work as real interactive quizzes
* conversations persist through backend APIs
* search works
* settings work
* light/dark mode works across the entire app
* responsive behavior is good
* loading/empty/error states exist
* API errors are handled cleanly
* frontend tests pass
* no AI/API secrets exist in the frontend
* no AI Engine logic is duplicated in the frontend

---

# 30. Implementation Rules for Antigravity

1. Read this file completely before coding.
2. Inspect the existing FastAPI backend and its OpenAPI contract.
3. Inspect the existing AI Engine only to understand backend behavior; do not modify it.
4. Use JavaScript, not TypeScript.
5. Follow the technology stack in this document.
6. Build a reusable component system.
7. Build the layout and routing foundation before implementing individual feature pages.
8. Keep API calls in service/hooks layers, not directly in page markup.
9. Use TanStack Query for server state.
10. Implement light/dark mode as a first-class feature, not as a final patch.
11. Use primary colors and semantic accents; avoid making purple the dominant color.
12. Do not invent backend endpoints. Use the existing FastAPI API contract.
13. If an API required by the UI is missing, report it clearly instead of silently mocking it in production code.
14. Use realistic loading/error/empty states.
15. Do not add unnecessary dependencies.
16. Keep the UI responsive and accessible.
17. Run tests and build checks regularly.
18. Do not rewrite working backend or AI Engine code just to accommodate the frontend.

---

# 31. Required First Step

Before implementing the frontend:

1. Read this specification completely.
2. Inspect the current repository.
3. Inspect `BACKEND_IMPLEMENTATION.md`.
4. Inspect the FastAPI routes and OpenAPI schema.
5. Identify the actual API request/response contracts.
6. Produce a frontend implementation plan based on the existing backend.
7. Identify any API gaps that prevent a page from being implemented correctly.
8. Do not write frontend implementation code until the plan and API mapping are understood.

Then build the frontend using the architecture and rules above.
