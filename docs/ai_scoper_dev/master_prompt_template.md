# AI Jira Scoper & Task Generator: Master Build Prompt

Copy and paste the prompt below into any AI coding assistant or LLM to build the entire project from scratch.

---

```text
You are a senior full-stack developer and UI designer. Build the "AI Jira Scoper & Task Generator" web application using Node.js/Express for the backend and Vanilla HTML5/CSS3/JavaScript for the frontend.

The application must be completely self-contained, look premium with Dracula-style glassmorphism highlights, support 5 customizable color schemes, and focus on expanding software concepts into Jira-importable Epics, Stories/Tasks, and Subtasks.

Implement the following structure:

### 1. Folder Layout
- projects/ai-scoper-app/
  - package.json (Express, mammoth, pdf-parse, jest, supertest)
  - server.js (REST server and exporters)
  - llmClient.js (Multi-connector helper class)
  - documentParser.js (DOCX, PDF, CSV, XML text parsers, and base64 images)
  - securityScanner.js (PII & sensitive credential scrubs)
  - public/
    - index.html (Main SPA layout)
    - style.css (Custom color themes & glassmorphism layout)
    - app.js (Front-end event controller)

---

### 2. Backend Implementation Spec

#### 2.1 API Routes:
- POST `/api/scan`: Checks text for private IPs, MAC addresses, emails, SSNs, and API keys. Returns matched count and indices.
- POST `/api/expand`: Sends concepts to the LLM. The system instruction must enforce:
  "You are a senior Jira project manager. Generate a highly structured list of Jira Epics (# Epic:), Tasks (## Task:), and Subtasks (### Subtask:). Include descriptions and suggested labels (e.g. 'Labels: auth, infra') on a new line."
- POST `/api/interview/questions`: Generates 5 scoping questions to resolve gaps.
- POST `/api/analyze/vulnerabilities`: Returns security critiques and architectural alternatives.
- POST `/api/prompt/generate`: Combiles the final scoping prompt.
- POST `/api/prompt/tune`: Chat-based tuner using conversational history to modify the prompt.
- POST `/api/syntax/check`: Validates pasted code snippets:
  - Python: executes `python3 -m py_compile` locally.
  - Node/JS: executes basic javascript syntax parser loops.
- POST `/api/export`: Generates downloadable file formats:
  - CSV Format: MUST parse the hierarchical markdown tree:
    - # Epic: -> row with type 'Epic'
    - ## Task: -> row with type 'Task', parent points to Epic ID
    - ### Subtask: -> row with type 'Sub-task', parent points to Task ID
    - Column headers: "Issue ID", "Summary", "Description", "Issue Type", "Parent ID", "Labels".

---

### 3. Frontend Specifications

#### 3.1 Color Schemes (CSS Variable Overrides):
Define 5 distinct themes applied via class selection on the `<body>`:
1. `theme-dracula` (Default): obsidian grey (#1e1f29) with neon pink (#ff79c6) and purple (#bd93f9).
2. `theme-nord`: arctic slate (#2e3440) with frost blue (#88c0d0).
3. `theme-gruvbox`: retro warm charcoal (#1d2021) with yellow (#fabd2f) and aqua (#8ec07c).
4. `theme-onedark`: Atom dark (#21252b) with soft blue (#61afef) and purple (#c678dd).
5. `theme-solarized`: oceanic teal (#002b36) with deep magenta (#d33682) and green (#859900).

All panels must use glassmorphism card styling:
- Subtle top border highlight: `border-top: 1px solid rgba(255, 255, 255, 0.08)`
- Deep bottom shadow: `border-bottom: 1px solid rgba(0, 0, 0, 0.45); box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5)`
- Globally rounded corners (`12px`).

#### 3.2 SPA Navigation:
Implement 5 tab views:
1. Jira Task Expansion: Input textbox, file dropzone, redaction overlays, and spec preview cards.
2. Scoping Interview: Dynamic list of questions with text inputs and submit buttons.
3. Security & Alternatives: Display area showing vulnerability critiques.
4. Syntax Checker: Language dropdown selector and validation logs.
5. Prompt Tuner: Side-by-side layout: left has draft textarea + export formats dropdown, right has conversational tuning chat.

#### 3.3 State Controls:
- Keyup trigger on Concept area to live-scan and show/hide the "Redaction Warning" overlay.
- Dragover/drop listeners on file upload to parse content in the browser (handling Docx/PDF text rendering and Image-to-base64 streams).
- LocalStorage state persistence of the selected color scheme theme.
- Visual format commands to fix messy markdown table borders and normalize headings on the fly.
```
