# StudyPilot Visual & UX Design System Specification

## 1. Design Philosophy

StudyPilot is built as a **high-focus, modern academic productivity workspace**. The design philosophy emphasizes:

- **Primary-Color Driven Clarity**: Clean slate/white base with purposeful semantic accents. Blue drives primary navigation and actions; Green signals ready/success states; Orange highlights study actions and quizzes; Red handles errors and deletions; Cyan/Teal represents AI system signals; Purple is strictly a restrained secondary accent.
- **Calm Cognitive Ergonomics**: High information density without visual chaos. Compact cards, clear typography hierarchy, and structured grids allow students to process long documents, dense transcripts, and complex RAG answers with minimal fatigue.
- **First-Class Dual Theme (Light & Dark)**: Semantic color variables guarantee high contrast and zero visual breakage whether studying in bright daylight or late-night dark mode.
- **Grounded AI Transparency**: Every AI response explicitly links to source document chunks with clear citation badges, page indicators, and expandable context panels.
- **Keyboard-First Flow**: Fast navigation, multi-line chat composition, accessible focus states, and zero shifts on hover.

---

## 2. Brand Identity

- **Wordmark**: `StudyPilot` rendered in `Plus Jakarta Sans` or `Inter` (Font Weight 700 / Bold). The word "Study" uses the primary text color (`text-slate-900` / `text-slate-50`), while "Pilot" uses Primary Blue (`text-blue-600` / `text-blue-400`).
- **Logo / Mark**: A geometric compass-spark icon inside a rounded square badge (`bg-blue-600` with white vector paths), symbolizing guided academic discovery.
- **Iconography**: Exclusively Lucide React SVG icons (24x24 viewBox, stroke-width 2px). **Never use emojis as UI icons**.
  - Dashboard: `LayoutDashboard`
  - Resources: `FileText` (PDF), `Video` (YouTube), `Folder`
  - Chat / Workspace: `MessageSquare`, `Sparkles`, `Send`
  - Summary: `BookOpen`, `FileCheck`
  - Notes: `NotebookPen`, `ListCheck`
  - Quiz: `HelpCircle`, `Award`, `CheckCircle2`
  - Search: `Search`, `Filter`
  - Settings: `Settings`, `User`, `Moon`, `Sun`
  - Actions: `Trash2`, `Copy`, `RotateCw`, `ExternalLink`, `ChevronRight`

---

## 3. Color System

### Semantic Token Matrix

| Role | Light Theme (HEX / Class) | Dark Theme (HEX / Class) | Functional Purpose |
| :--- | :--- | :--- | :--- |
| **Canvas Background** | `#F8FAFC` (`bg-slate-50`) | `#0F172A` (`bg-slate-900`) | Main application viewport backdrop |
| **Surface (Cards/Modals)**| `#FFFFFF` (`bg-white`) | `#1E293B` (`bg-slate-800`) | Elevating content cards and panels |
| **Muted Surface** | `#F1F5F9` (`bg-slate-100`) | `#334155` (`bg-slate-700/50`) | Input backgrounds, code blocks, chat bubbles |
| **Border / Divider** | `#E2E8F0` (`border-slate-200`) | `#334155` (`border-slate-700`) | Card outlines, tab separators |
| **Primary Text** | `#0F172A` (`text-slate-900`) | `#F8FAFC` (`text-slate-50`) | Headings, primary body content |
| **Secondary Text** | `#475569` (`text-slate-600`) | `#94A3B8` (`text-slate-400`) | Subtitles, metadata, timestamps |
| **Primary Action (Blue)**| `#2563EB` (`bg-blue-600`) | `#3B82F6` (`bg-blue-500`) | Primary buttons, active nav, focus rings |
| **Success / Ready (Green)**| `#16A34A` (`bg-green-600`) | `#22C55E` (`bg-green-500`) | Processing ready status, correct answers |
| **Study / Warning (Orange)**| `#D97706` (`bg-amber-600`) | `#F59E0B` (`bg-amber-500`) | Quiz action, processing state, attention |
| **Destructive / Error (Red)**| `#DC2626` (`bg-red-600`) | `#EF4444` (`bg-red-500`) | Delete actions, error banners, YouTube tag |
| **AI System / Citations**| `#0D9488` (`bg-teal-600`) | `#14B8A6` (`bg-teal-500`) | Grounded citation badges, AI model info |
| **Restrained Accent (Purple)**| `#9333EA` (`text-purple-600`)| `#C084FC` (`text-purple-400`) | Quiz score highlights, minor badges only |

---

## 4. Typography

Font Family: `Inter`, `Plus Jakarta Sans`, system-ui, sans-serif.

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
```

### Scale & Hierarchy

| Usage | Size | Line Height | Weight | Tailwind Classes |
| :--- | :--- | :--- | :--- | :--- |
| **Display / Hero** | 2rem (32px) | 1.25 | Bold (700) | `text-3xl font-bold tracking-tight` |
| **Heading 1 (H1)** | 1.5rem (24px) | 1.3 | SemiBold (600) | `text-2xl font-semibold tracking-tight` |
| **Heading 2 (H2)** | 1.25rem (20px) | 1.35 | SemiBold (600) | `text-xl font-semibold` |
| **Heading 3 (H3)** | 1.125rem (18px) | 1.4 | Medium (500) | `text-lg font-medium` |
| **Body (Normal)** | 0.875rem (14px) | 1.5 | Normal (400) | `text-sm font-normal` |
| **Body (Medium)** | 0.875rem (14px) | 1.5 | Medium (500) | `text-sm font-medium` |
| **Label / Button** | 0.875rem (14px) | 1.25 | SemiBold (600) | `text-sm font-semibold` |
| **Caption / Meta** | 0.75rem (12px) | 1.4 | Normal (400) | `text-xs font-normal` |

---

## 5. Spacing System

Base Unit: 4px scale.

| Token | Pixels | Usage |
| :--- | :--- | :--- |
| `space-1` | 4px | Micro gaps, icon-to-text spacing |
| `space-2` | 8px | Button inline padding, badge padding, tight stack |
| `space-3` | 12px | Input internal padding, card internal gap |
| `space-4` | 16px | Container padding, grid gap (compact) |
| `space-6` | 24px | Card padding, section spacing, page gutter |
| `space-8` | 32px | Major section margins, modal padding |
| `space-12`| 48px | Page hero header spacing |

---

## 6. Border & Radius System

- **Card Radius**: `rounded-xl` (`12px`) for cards, sidebars, and panels.
- **Button / Input Radius**: `rounded-lg` (`8px`) for buttons, text fields, and select dropdowns.
- **Badge Radius**: `rounded-full` (`9999px`) for status pills and tags.
- **Modal Radius**: `rounded-2xl` (`16px`) for dialogs and modal overlays.
- **Border Style**: `1px solid` using `border-slate-200` (Light) or `border-slate-700` (Dark).

---

## 7. Shadow / Elevation System

- **Level 0 (Flat)**: `shadow-none` (Used inside cards or nested lists).
- **Level 1 (Subtle Card)**: `shadow-sm` (`0 1px 2px 0 rgb(0 0 0 / 0.05)`).
- **Level 2 (Hover Card / Dropdown)**: `shadow-md` (`0 4px 6px -1px rgb(0 0 0 / 0.1)`).
- **Level 3 (Modal / Floating Drawer)**: `shadow-xl` (`0 20px 25px -5px rgb(0 0 0 / 0.1)`).

---

## 8. Button Guidelines

### Variants

- **Primary**: `bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-sm transition-colors duration-150 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:ring-offset-2`
- **Secondary / Muted**: `bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-900 dark:text-slate-100 font-medium rounded-lg px-4 py-2 text-sm`
- **Outline**: `border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-lg px-4 py-2 text-sm`
- **Ghost**: `hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-lg px-3 py-1.5 text-sm`
- **Destructive**: `bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg px-4 py-2 text-sm`
- **Icon-Only**: `p-2 rounded-lg text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800`

### States
- **Loading**: Disables pointer events, shows animated inline spinner icon, opacity 75%.
- **Disabled**: `opacity-50 cursor-not-allowed pointer-events-none`.

---

## 9. Form Controls

- **Text Inputs & Textareas**:
  - Light: `bg-white border-slate-300 text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20`
  - Dark: `bg-slate-800 border-slate-700 text-slate-100 placeholder:text-slate-500 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20`
- **Validation Error State**: Adds `border-red-500 focus:border-red-500 focus:ring-red-500/20`, renders helper message below input in `text-xs text-red-500`.

---

## 10. Cards & Containers

- **Standard Content Card**: `bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm`
- **Interactive Clickable Card**: `hover:border-blue-500 dark:hover:border-blue-400 hover:shadow-md cursor-pointer transition-all duration-200`

---

## 11. Navigation System

### Sidebar Navigation
- Width: Fixed `256px` (`w-64`) on desktop; Collapsible to `72px` (`w-18`); Slide-over drawer on mobile (`<768px`).
- Item Layout: Left-aligned Lucide icon + label text + count badge.
- Active Item Style: `bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 font-semibold border-r-4 border-blue-600`.

### Topbar Navigation
- Height: `64px` (`h-16`). Border bottom `border-slate-200` / `border-slate-700`.
- Left: Breadcrumb / Active Page Title.
- Right: Quick Search Trigger (`Ctrl+K`), Theme Switcher Button, Notifications Icon, User Profile Avatar.

---

## 12. Resource UI System

### PDF vs YouTube Visual Identity
- **PDF Resource**: Blue-accent badge (`bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300`), Lucide `FileText` icon.
- **YouTube Resource**: Red-accent badge (`bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300`), Lucide `Video` icon.

### Status Indicators
- **Ready State**: Green pill badge (`bg-green-100 dark:bg-green-950 text-green-700 dark:text-green-300`), label `"Ready"`.
- **Processing State**: Amber pill badge (`bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300`), spinning icon, label `"Processing"`.
- **Failed State**: Red pill badge (`bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-300`), label `"Failed"`.

### Upload Dropzone UI
- Border: `2px dashed border-slate-300 dark:border-slate-700 hover:border-blue-500 rounded-2xl p-8 text-center bg-slate-50/50 dark:bg-slate-800/50 cursor-pointer`.
- Primary CTA: "Click to upload PDF or drag & drop". Max size indicator "Up to 50MB".

---

## 13. Study Workspace & AI Chat UI

### 3-Panel Workspace Grid Layout
- **Left Panel (History/Scope)**: `w-64 border-r border-slate-200 dark:border-slate-700`. Lists conversation threads and resource selector.
- **Center Panel (Chat Thread)**: `flex-1 flex flex-col`. Displays message list with composer at bottom.
- **Right Panel (Grounded Citations)**: `w-80 border-l border-slate-200 dark:border-slate-700`. Slide-over drawer on mobile screens.

### Message Bubbles
- **User Message**: Aligned right. `bg-blue-600 text-white rounded-2xl rounded-tr-sm p-4 max-w-[80%]`.
- **Assistant Message**: Aligned left. `bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-2xl rounded-tl-sm p-4 max-w-[85%] border border-slate-200/50 dark:border-slate-700/50`.

### Grounded Source Citations
- Citation Pill: `inline-flex items-center gap-1 bg-teal-50 dark:bg-teal-950/60 border border-teal-200 dark:border-teal-800 text-teal-700 dark:text-teal-300 text-xs px-2 py-0.5 rounded-md cursor-pointer hover:bg-teal-100`.
- Clicking citation pill expands corresponding chunk details in the Right Citation Panel with match score percentage.

---

## 14. Summary UI

- **Header Card**: Shows Resource Title, Generation Date, Config Hash tag, and Cache Status Pill (`Cached` = Green, `Fresh` = Cyan).
- **Control Bar**: Actions for `Copy Text`, `Export PDF`, and `Regenerate Fresh` (with explicit loading indicator).
- **Summary Body**: Formatted markdown with structured sections, executive summary box, and bullet points.

---

## 15. Notes UI

- **Style Selector**: Toggle Tabs (`Bullet Notes` vs `Cornell Notes`).
- **Bullet Notes Layout**: Hierarchical lists with icon bullets (`ListCheck`), bolded concept terms, and clear spacing.
- **Cornell Notes Layout**:
  - 2-Column Section: Left column (`Cue / Key Concepts` - 30% width), Right column (`Main Notes & Explanations` - 70% width).
  - Bottom Box: `Summary & Key Takeaways` (`bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 p-4 rounded-xl`).

---

## 16. Quiz UI

### Quiz Runner Experience
- **Progress Header**: Question counter ("Question 3 of 5") + Visual Progress Bar (`bg-amber-500`).
- **Question Card**: Bold question text (`text-lg font-semibold mb-4`).
- **Option Cards**: Radio button list (`border-slate-200 dark:border-slate-700 hover:border-amber-400 p-4 rounded-xl cursor-pointer flex items-center justify-between`).
- **Selection State**: `border-2 border-amber-500 bg-amber-50/30 dark:bg-amber-950/20`.

### Submission & Answers Policy
- **STRICT UX RULE**: Correct answers and explanations MUST NOT be revealed while answering.
- Upon clicking `Submit Answer`:
  - Correct Option: Green highlight (`bg-green-100 dark:bg-green-950 border-green-500 text-green-800 dark:text-green-200`).
  - Incorrect Selected Option: Red highlight (`bg-red-100 dark:bg-red-950 border-red-500 text-red-800 dark:text-red-200`).
  - Explanation Card: Appears below question in `bg-slate-100 dark:bg-slate-800 p-4 rounded-xl border-l-4 border-blue-500`.

---

## 17. Conversation UI

- **Conversation List Item**: Title text, timestamp ("2 hours ago"), associated resource tag, message count badge (`bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs px-2 py-0.5 rounded-full`), and delete trash icon.
- **Active Conversation Detail**: Full conversation turn history with search-within-chat bar.

---

## 18. Search UI

- **Global Search Bar**: `w-full max-w-2xl text-base py-3 px-4 pl-12 rounded-xl border border-slate-300 dark:border-slate-600 shadow-sm`.
- **Search Results Grid**: Categorized tabs (`All`, `Resources`, `Conversations`, `Notes`).
- **Result Item**: Title, matched excerpt snippet with search terms highlighted, resource type badge, and direct navigation arrow.

---

## 19. Settings UI

- **Tabbed Layout**:
  - `Profile`: Avatar, Full Name input, Email input (read-only), Member since date.
  - `Appearance`: Radio cards for `Light`, `Dark`, `System` with visual theme preview miniatures.
  - `Preferences`: Default summary mode, preferred quiz question count (5, 10, 15).
  - `Account`: Logout button (`bg-red-600 text-white`).

---

## 20. Authentication UI

- **Auth Container Layout**: Centered card (`max-w-md w-full p-8 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-xl`).
- **Brand Header**: StudyPilot logo, heading ("Welcome back"), subtitle ("Sign in to your account to continue studying").
- **Form Controls**: Email input, Password input with toggle show/hide icon, inline validation error text.
- **Primary CTA**: Full-width Primary Blue button ("Sign In" / "Create Account").

---

## 21. Feedback States

- **Loading Skeleton**: Shimmering background (`animate-pulse bg-slate-200 dark:bg-slate-700 rounded-lg`).
- **Empty State**: Centered illustration icon (`FileText` or `MessageSquare`), friendly heading ("No resources added yet"), descriptive text, and Primary Blue action button.
- **Error State**: Red banner (`bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-800 p-4 rounded-xl flex items-center gap-3 text-red-800 dark:text-red-200`) with Retry button.
- **Toast Notifications**: Floating top-right alert box (`shadow-lg border p-4 rounded-xl flex items-center gap-3 bg-white dark:bg-slate-800`).

---

## 22. Responsive Design Grid

- **Desktop (1440px+)**: Full 3-panel chat workspace, persistent sidebar (`256px`), multi-column card grids (`grid-cols-3`).
- **Laptop (1024px)**: Collapsed sidebar (`72px`), 2-panel chat workspace with toggleable citation drawer, 2-column card grids.
- **Tablet (768px)**: Slide-over navigation drawer, single-column dashboard cards, resource table switches to card list.
- **Mobile (375px)**: Fullscreen chat composer, single-column quiz cards (1 question per screen), stacked buttons.

---

## 23. Accessibility Standards

- **Contrast Ratio**: 4.5:1 minimum for body text against backgrounds; 3:1 minimum for large headings.
- **Focus Rings**: `focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-slate-900`.
- **Keyboard Navigation**: Full Tab key traversal for form fields, Escape key to close modal dialogs, Enter/Space key to toggle buttons.
- **Screen Reader Labels**: `aria-label` added to all icon-only buttons (`aria-label="Delete resource"`).

---

## 24. Motion & Micro-Interactions

- **Allowed Micro-Interactions**:
  - Color & opacity transitions (`transition-colors duration-150 ease-in-out`).
  - Modal overlay fade-in (`opacity-0` to `opacity-100` in 200ms).
  - Drawer slide-in (`translate-x-full` to `translate-x-0` in 250ms).
- **Prohibited Motion**:
  - Scale transforms that shift layout on hover.
  - Infinite floating or bouncing decorative animations.

---

## 25. Light / Dark / System Theme Architecture

```javascript
// Theme Application Logic
const applyTheme = (theme) => {
  const root = document.documentElement;
  const isDark = theme === 'dark' || 
    (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
  
  if (isDark) {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
  localStorage.setItem('studypilot_theme', theme);
};
```

---

## 26. Page-Level Design Guidance

### 1. DashboardPage
- **Layout**: Top Welcome Banner -> Quick Action Cards Grid (4 cols) -> Recent Resources List & Recent Conversations List (2 cols).
- **Primary CTA**: "Upload New Resource" (Primary Blue Button).

### 2. ResourcesPage
- **Layout**: Top Filter Header (Search input, Type select, Upload CTA) -> Resource Cards/Table Grid.
- **Primary CTA**: "+ Add Resource" (Primary Blue Button opening Upload Modal).

### 3. ResourceDetailPage
- **Layout**: Top Metadata Header -> Resource Action Cards Grid (Start Chat, View Summary, View Notes, Take Quiz).
- **Primary CTA**: "Start Chat Session" (Primary Blue Button).

### 4. StudyWorkspacePage
- **Layout**: 3-Panel Grid (Conversations Sidebar, Chat Thread + Composer, Citation Context Panel).
- **Primary CTA**: Send Message Button (`Send` icon button).

### 5. SummariesPage
- **Layout**: Header (Title, Cache Status Pill) -> Toolbar (Copy, Export, Regenerate) -> Markdown Summary Card.
- **Primary CTA**: "Regenerate Summary" (Secondary Button with loading spinner).

### 6. NotesPage
- **Layout**: Style Tabs (Bullet vs Cornell) -> Notes Content Container with Copy Button.
- **Primary CTA**: "Generate Notes" (Amber Button).

### 7. QuizPage
- **Layout**: Progress Header -> Single Question Card -> Options Radio List -> Submit/Next Button.
- **Primary CTA**: "Submit Answer" (Amber Button).

### 8. ConversationsPage
- **Layout**: Conversation Threads List -> Message History Detail Drawer.
- **Primary CTA**: "+ New Conversation" (Primary Blue Button).

### 9. SearchPage
- **Layout**: Centered Global Search Input -> Categorized Results List.
- **Primary CTA**: Search Submit Button.

### 10. SettingsPage
- **Layout**: Tabbed Settings Form (Profile, Appearance, Preferences, Account).
- **Primary CTA**: "Save Preferences" (Primary Blue Button).

### 11. LoginPage / RegisterPage
- **Layout**: Centered Auth Card on slate backdrop.
- **Primary CTA**: "Sign In" / "Register" (Full-width Primary Blue Button).

### 12. ErrorPage / NotFoundPage
- **Layout**: Centered Error Graphic, status code ("404"), explanation text, and "Return to Dashboard" button.
