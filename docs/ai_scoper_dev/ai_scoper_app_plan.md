# Implementation Plan: AI Jira Scoper & Task Generator Web Application

This plan outlines the architecture, features, and verification strategy for a local, premium single-page web application designed to expand product concepts, conduct scoping interviews, scan for vulnerabilities/issues, check code syntax, and generate **highly structured Jira Epics, Tasks, and Subtasks** formatted for direct import.

---

## 1. Product Specification & User Interface

The application will be built as a single-page web app using **Vanilla HTML5, CSS3, and JavaScript (ES6)** for the front-end, and **Node.js / Express** for the backend.

### UI Styling & Color Schemes
The interface utilizes CSS Custom Properties (Variables) to allow switching between **5 distinct, developer-centric color schemes** dynamically:
1. **Dracula (Default)**: Deep obsidian grey background (`#1e1f29`) with vibrant neon pink, purple, and green highlights.
2. **Nord**: Cool arctic slate background (`#2e3440`) with clean frost blue and muted snowstorm white text highlights.
3. **Gruvbox**: Retro warm charcoal background (`#1d2021`) with organic yellow, orange, and aqua highlights.
4. **One Dark**: Modern soft atom dark background (`#21252b`) with purple, soft green, and sky blue accents.
5. **Solarized Dark**: Classic high-contrast oceanic teal background (`#002b36`) with deep blue, magenta, and cyan highlights.

* **Beveled Card Aesthetics**: All themes implement glassmorphic card layers with a light top border (`1px solid rgba(255,255,255,0.08)`) and a darker bottom drop-shadow (`1px solid rgba(0,0,0,0.45)`).
* **Typography**: DM Sans / Inter for readable UI content, JetBrains Mono for code blocks.

### Core App Views & Tabs (Focused on Jira Tasking)
```mermaid
graph TD
    Dashboard[Dashboard Shell] --> Tab1[1. Jira Task Expansion]
    Dashboard --> Tab2[2. Scoping Interview]
    Dashboard --> Tab3[3. Security & Alternatives]
    Dashboard --> Tab4[4. Syntax & Code Checker]
    Dashboard --> Tab5[5. Prompt Tuner]
    
    Tab1 -->|AI Call| Exp[Epic, Story, & Subtask Hierarchy]
    Tab2 -->|Interactive Q&A| Ques[AI-generated Clarification Questions]
    Tab3 -->|Security Scan| Vulnerabilities[Threats & Design Alternatives]
    Tab4 -->|Code Validator| Check[Language Lint/Syntax Engine]
    Tab5 -->|Prompt Builder| SystemPrompt[Unified Master Coding Prompt]
```

---

## 2. Proposed Changes & Code Structure

We will initialize the project under the `projects/ai-scoper-app/` directory:

### Backend Services (`projects/ai-scoper-app/server.js`)
An Express server implementing the following modules and REST endpoints:

* **Pluggable LLM client module (`projects/ai-scoper-app/llmClient.js`)**:
  - Exposes a unified client class interface that supports:
    - **Google Gemini** (via `@google/generative-ai` or REST API)
    - **OpenAI ChatGPT** (via `openai` SDK or REST API)
    - **Anthropic Claude** (via `@anthropic-ai/sdk` or REST API)
    - **xAI Grok** (via custom Grok REST API endpoint or OpenAI-compatible client configuration)
    - **Internal/Local LLM** (allows users to specify custom Base URLs e.g. `http://localhost:11434/v1` for Ollama, model identifiers, and custom authentication headers).
  - Dynamically routes LLM generation requests to the chosen provider based on client headers.

* **Multi-Format Document Parser (`projects/ai-scoper-app/documentParser.js`)**:
  - Handles parsing of incoming files:
    - **Text-based**: CSV, Markdown, HTML, XML, JSON, Plain Text.
    - **Word Docs**: Uses the `mammoth` library to extract clean text from `.docx` files.
    - **PDF Docs**: Uses the `pdf-parse` library to extract plaintext.
    - **Images & Attachments**: Accepts image attachments (PNG, JPEG, WebP, GIF), converting them to Base64 buffers and forwarding them to multimodal-enabled LLMs (e.g. Gemini 1.5 Pro, GPT-4o, Claude 3.5 Sonnet) for visual analysis and transcription.

* **Security & Sensitive Data Scanner (`projects/ai-scoper-app/securityScanner.js`)**:
  - Pre-scans all inputs before forwarding to external LLMs.
  - Automatically flags and masks:
    - **PII**: Email addresses, SSNs, phone numbers.
    - **Networking**: IP addresses (IPv4 & IPv6), MAC addresses, internal hostnames.
    - **Secrets**: API keys (AWS Access Key ID, GitHub tokens, Slack Webhooks, etc.), private keys, 2FA backup seeds, usernames, passwords.

* **Rest Endpoints**:
  * `POST /api/scan`: Runs the input through the Security Scanner, returning matched tokens and offering masking.
  * `POST /api/expand`: Accepts parsed document text and image attachments, and uses the configured LLM to generate a structured **Jira Task tree** containing Epics, child Stories/Tasks, and Subtasks, complete with descriptions and tags.
  * `POST /api/interview/questions`: Generates clarificatory questions about functionality and features.
  * `POST /api/analyze/vulnerabilities`: Scans the architectural design for security flaws, host vulnerabilities, and offers design alternatives.
  * `POST /api/prompt/generate`: Compiles the master coding prompt and maps task lists.
  * `POST /api/prompt/tune`: Uses LLM conversing to adjust the system prompt or the task list structure.
  * `POST /api/syntax/check`: Performs compile-check assertions on pasted code snippets.
  * `POST /api/export`: Packages the generated scoping documents and compiles a **Jira CSV Import file** (mapping `Summary`, `Description`, `Issue Type`, `Parent ID`, `Labels`) for seamless direct import.
  * `GET /api/plan`: Serves the HTML-rendered implementation plan (`ai_scoper_app_plan.md`) directly in the user's web browser.
  * `GET /api/docs/:filename`: Serves any HTML-rendered markdown file (e.g. `walkthrough`, `jira_task_breakdown`, `jira_token_guide`) dynamically in the browser.

### Frontend App (`projects/ai-scoper-app/public/index.html` & `style.css` & `app.js`)
* **LLM Config Drawer**: Sidebar dropdowns to select the active provider (Gemini, ChatGPT, Claude, Grok, or Custom Internal LLM) and input custom API keys, model endpoints, and baseURL headers.
* **Universal File & Image Dropzone**: Drag-and-drop zone that extracts content from PDF, DOCX, CSV, XML, or Text uploads, alongside image and file attachment thumbnail previews.
* **Sensitive Data Redaction Overlay**: Renders alerts highlighting detected IP addresses, API keys, or usernames with a "Redact All" button before processing.
* **Jira Task Hierarchy Review Pane**:
  - Displays the AI-expanded specifications as a structured tree layout (Epic cards containing child Story boxes with expandable Subtask bullet points).
  - A visual editing toolbar to quickly fix tables, edit headings, adjust font types, modify theme colors, and clean up the overall document structure on the fly.
  - Auto-format helpers to clean up messy table layouts and auto-convert markdown structures.
* **Interactive Prompt Tuner**: Side-by-side comparison pane. The left shows the generated system prompt; the right is an AI chat panel where the user tells the AI to rewrite, expand, or adjust parts of the prompt, updating the generated draft in real-time.
* **Jira Exporter Dashboard**: Buttons to download generated deliverables in any user-selected format (.docx, .pdf, .md, .xml) or a **Jira-importable CSV file**.

### Master Prompt Template Artifact ([NEW] master_prompt_template.md)
* **Goal**: Generate a single-file, self-contained master system prompt that instructs any standard LLM on how to build, layout, and validate this entire application from scratch (incorporating CSS themes, parser libraries, regex scrubbers, syntax compiles, and Jira import structures).

### Jira API Token Guide Artifact ([NEW] jira_token_guide.md)
* **Goal**: Document step-by-step instructions on how users can create and manage their Atlassian Jira Cloud API tokens securely.

### Jira Automation Script ([NEW] python/upload_jira_tasks.py)
* **Goal**: Implement a Python script that parses the markdown backlog file `jira_task_breakdown.md`, maps issue relationships (Epics, Stories/Tasks, Subtasks), and utilizes the Jira Cloud REST API to programmatically provision the `AutoTask-Ai-Generator` project (Key: `ATA`) and import the issues. Sensitive credentials (`JIRA_URL`, `JIRA_USER`, `JIRA_API_TOKEN`) will be read dynamically from environment variables.

### Document Publishing Deployment
* **Goal**: Copy all 6 project markdown specification and guide files (including plans, walkthroughs, backlogs, prompt templates, and token guides) from the session's artifact directory to `/home/rtroiano/repositories/scripts-public/docs/ai_scoper_dev/` for public versioning.

### Git Release & Push Deployment
* **Goal**: Perform local repository staging, commit the files with descriptive commit logs, and push modifications to their remote origins in both `/home/rtroiano/repositories/scripts` and `/home/rtroiano/repositories/scripts-public` workspaces.

### Public File URL Mapping
* **Goal**: Document and map the exact local paths and public GitHub repository links for all 6 generated project files inside the `scripts-public` repository.

### Table of Contents Documentation ([NEW] README.md)
* **Goal**: Create a central `README.md` index file linking all 6 generated project files together with descriptions of each specification and direct links.

---

## 3. Verification Plan

### Git-Driven Testing & Interactive Change Review
* **Development Branching**:
  - All testing and changes will be conducted by programmatically creating a `dev` branch branched off of `main`.
  - The backend handles git actions (`git checkout -b dev`, checking active working state).
* **Rendered Markdown Change Review**:
  - When the AI executes instructions or modifies files/documents, the proposed changes are compiled and rendered in the web interface as styled Markdown.
  - The user interface displays a comparison diff pane showing:
    - **Before (Current)** vs **After (Proposed)** content.
* **Interactive Control Lifecycle**:
  - **Accept**: The user approves the change, and the backend commits the modification to the `dev` branch.
  - **Edit**: Toggles a raw text editor, allowing the user to manually tune the text before accepting/committing.
  - **Discard**: Discards the proposed change and resets the workspace.
  - **Regenerate**: Requests the LLM to rebuild the content from a different angle or structure to explore alternative ways of presenting the information.

### Automated Tests
* Unit tests for the document parsers (checking CSV, XML, PDF text extraction).
* Regex checks for PII/credentials scrubbing.
* Syntax validator test suite for JS/Python error assertions.

### Manual Verification Flow
1. **Startup Check**: Initialize the server using `node server.js` and verify it binds to `http://localhost:5070`.
2. **Git Branch Verification**: Verify that the application creates a `dev` branch from `main` upon project initialization.
3. **Change Control Verification**:
   - Make a request for a change (e.g. *"create a standard authentication endpoint"*).
   - Confirm the change shows in the UI as rendered markdown side-by-side.
   - Verify clicking **Edit** enables modification of the change.
   - Verify clicking **Discard** resets the workspace.
   - Verify clicking **Regenerate** re-invokes the LLM to present the details in a new/alternative layout.
   - Verify clicking **Accept** writes the final edits to the workspace files.
4. **LLM Provider Switching**: Configure OpenAI/Gemini/Claude keys. Toggle between providers and verify responses load.
5. **Format Ingestion Test**: Upload a `.pdf` design spec or a `.csv` list of tasks. Verify text is successfully loaded into the prompt workspace.
6. **Secrets Scrubbing Test**: Paste a text containing `192.168.1.80`, `AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE`, and `my-admin-password`. Verify the UI flags these items and replaces them with masked placeholders (e.g. `[REDACTED_IP]`) upon clicking "Redact".
7. **Interactive Tuning Test**: Generate a master prompt, type *"incorporate a PostgreSQL database schema with a users table"*, and check if the prompt updates to include SQL definitions.
8. **Syntax Engine Check**: Paste valid and invalid code and confirm compiler messages show.
9. **Multi-Format Export Test**: Export the result as Markdown (.md) and XML. Verify the files download with appropriate schemas and layout.
10. **Color Scheme Switching Test**: Select each of the 5 themes (Dracula, Nord, Gruvbox, One Dark, Solarized) in the dropdown. Verify body class updates, colors render properly, and the theme choice persists in LocalStorage upon browser reload.
11. **Jira Task Uploader Test**: Run the Python uploader script in dry-run mode or check that it handles missing environment variables securely and outputs parsing validation logs for all Epics, Tasks, and Subtasks.
12. **Documentation Publishing Verification**: Run `ls -la /home/rtroiano/repositories/scripts-public/docs/ai_scoper_dev/` and verify that all 6 project markdown files exist and contain appropriate metadata structures.
13. **Git Release Verification**: Run `git status` in both `/home/rtroiano/repositories/scripts` and `/home/rtroiano/repositories/scripts-public` directories to confirm working directories are clean, and verify git logs for successful remote pushes.
14. **Public File URL Verification**: Verify that the generated links correctly resolve to their corresponding local files and public GitHub repository paths.
15. **General Docs Endpoint Verification**: Verify that navigating to `http://localhost:5070/api/docs/walkthrough` and `http://localhost:5070/api/docs/jira_task_breakdown` successfully renders the corresponding HTML-formatted markdown files in the browser.
