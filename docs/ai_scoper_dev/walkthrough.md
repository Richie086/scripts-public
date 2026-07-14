# Walkthrough: AI Jira Scoper & Task Generator Web Application

We have completed the development and local verification of the **AI Jira Scoper & Task Generator** web application. Below is a detailed summary of the implemented modules, the visual layout design, and validation checks.

---

## 1. Visual Layout & User Interface Mockup

The user interface implements our premium Dracula Dark mode aesthetic, utilizing card-based depth, glassmorphism highlights, and responsive flexboxes. 

![AI Scoper UI Layout Mockup](/home/rtroiano/.gemini/antigravity-cli/brain/5bac2cd3-828d-42f1-a375-cc94a3a19bcf/ai_scoper_ui_mockup_1783993260557.jpg)

### UI Components Shown:
* **Sidebar LLM Config Drawer**: Select between Gemini, ChatGPT, Claude, Grok, or Custom Internal endpoints. Enter API keys, baseURLs, and target models.
* **Git Control Panel**: Click "Initialize Dev Branch" to run git operations locally.
* **Tab Navigation**: Swap between Jira Task Expansion, Scoping Interview, Security/Alternatives, Syntax Checker, and Prompt Tuner.
* **Drag-and-Drop Dropzone**: Handles docx, pdf, csv, xml, md, and image attachments.
* **Sensitive Data Redaction Banner**: Warns and scrub matches (IPs, API keys) on the fly.
* **Visual Editing Toolbar**: Format bold/italic text, sanitize tables, and fix headers.
* **Markdown Render Pane**: Inspect side-by-side spec breakdowns before accepting.

---

## 2. Implemented Codebase Modules

All files are structured under `projects/ai-scoper-app/`:
1. **[package.json](file:///home/rtroiano/repositories/scripts/projects/ai-scoper-app/package.json)**: Declares dependencies for file extraction (`mammoth`, `pdf-parse`), routing (`express`), and testing (`jest`, `supertest`).
2. **[llmClient.js](file:///home/rtroiano/repositories/scripts/projects/ai-scoper-app/llmClient.js)**: Unified API interface supporting Google Gemini, OpenAI, Claude, Grok, and custom local/internal baseURL connections (e.g. Ollama).
3. **[documentParser.js](file:///home/rtroiano/repositories/scripts/projects/ai-scoper-app/documentParser.js)**: Parses docx, pdf, csv, xml, and text documents, and converts image uploads into base64 buffers for multimodal support.
4. **[securityScanner.js](file:///home/rtroiano/repositories/scripts/projects/ai-scoper-app/securityScanner.js)**: Heuristic filter checking inputs for PII, API keys/AWS secrets, usernames/passwords, and IP/MAC configurations.
5. **[server.js](file:///home/rtroiano/repositories/scripts/projects/ai-scoper-app/server.js)**: Express REST API hosting endpoints for expansion, interview questions, security audits, prompt tuning, export actions, local compiler syntax checks, and git branch initializations.
6. **[index.html](file:///home/rtroiano/repositories/scripts/projects/ai-scoper-app/public/index.html)**, **[style.css](file:///home/rtroiano/repositories/scripts/projects/ai-scoper-app/public/style.css)**, and **[app.js](file:///home/rtroiano/repositories/scripts/projects/ai-scoper-app/public/app.js)**: Client-side styling and event logic for rendering and file management.

---

## 3. Verification & Validation Testing

### Automated Jest Tests
We wrote and ran Jest unit tests verifying the sensitive data scanner:
```bash
PASS tests/securityScanner.test.js
  Security and PII Scanner Module
    ✓ detects email addresses and SSNs (6 ms)
    ✓ detects public and private IP addresses (2 ms)
    ✓ detects API secrets and keys (1 ms)
    ✓ scrubs credentials and replaces with placeholders (1 ms)
```

### Manual REST API Verification
1. **Express Server Boot**: Confirmed startup binding on `http://localhost:5070`.
2. **Scrubber Endpoint**: Verified POST `/api/scan` detects email addresses correctly:
   ```json
   {"vulnerabilities":[{"type":"EMAIL","token":"test@example.com","index":12,"severity":"LOW","description":"Detected potential sensitive email: \"test@example.co...\""}],"matchedCount":1}
   ```
3. **Jira CSV Importer Parser**: Verified that `/api/export` successfully parses Markdown task trees into standard, import-ready Jira CSV files, preserving parent-child hierarchical relations (`Issue ID` -> `Parent ID` links):
   * **Input**:
     ```markdown
     # Epic: User Authentication
     Labels: auth-v1
     ## Task: Set up Cognito
     Set up Cognito pool client.
     Labels: aws, cognitio
     ### Subtask: CF Script
     Write CloudFormation template.
     ```
   * **CSV Output**:
     ```csv
     "Issue ID","Summary","Description","Issue Type","Parent ID","Labels"
     "1","User Authentication","","Epic","","auth-v1"
     "2","Set up Cognito","Set up Cognito pool client.","Task","1","aws, cognitio"
     "3","CF Script","Write CloudFormation template.","Sub-task","2",""
     ```
4. **Local Syntax Engine**: Verified Python indentation and colon checks work locally:
   * Valid: `{"success":true,"message":"Syntax Check Passed successfully."}`
   * Invalid: `{"success":false,"error":"SyntaxError: expected ':'"}`
5. **Color Theme Switcher**: Verified dropdown selections switch between `theme-dracula`, `theme-nord`, `theme-gruvbox`, `theme-onedark`, and `theme-solarized` class structures, rendering matching color overrides. Reloading the page successfully reads from `LocalStorage` and preserves the last chosen theme state.
6. **Master Build Prompt**: Verified the generation of the self-contained [master_prompt_template.md](file:///home/rtroiano/.gemini/antigravity-cli/brain/5bac2cd3-828d-42f1-a375-cc94a3a19bcf/master_prompt_template.md) containing full rebuild parameters.
7. **Plan Browser View**: Verified that navigating to `http://localhost:5070/api/plan` renders the complete implementation plan document in the web browser with readable headers and styling.
8. **Jira Task Backlog**: Created the [jira_task_breakdown.md](file:///home/rtroiano/.gemini/antigravity-cli/brain/5bac2cd3-828d-42f1-a375-cc94a3a19bcf/jira_task_breakdown.md) backlog listing all Epics, Tasks, and Subtasks required to complete, test, and deploy the application.
9. **Jira Task Uploader**: Implemented and compiled [upload_jira_tasks.py](file:///home/rtroiano/repositories/scripts/python/upload_jira_tasks.py), successfully verifying dry-run parsing of all 5 Epics, 15 Tasks, and nested Subtasks.
10. **Jira API Token Guide**: Generated the step-by-step [jira_token_guide.md](file:///home/rtroiano/.gemini/antigravity-cli/brain/5bac2cd3-828d-42f1-a375-cc94a3a19bcf/jira_token_guide.md) guide file outlining token credentials setup.
11. **Documentation Publishing**: Verified that all 7 project markdown specs, plans, indices, and walkthrough files have been successfully copied to the public documentation directory `/home/rtroiano/repositories/scripts-public/docs/ai_scoper_dev/`.
12. **Git Release & Remote Push**: Verified staging, commits, and pushes to remote origins:
    - Public repo (`scripts-public`): Pushed code and docs to branch `master`.
    - Private repo (`scripts`): Pushed all application changes to feature branch `cursor/idea-tracker-1f3c`.
13. **Documentation Table of Contents**: Created the central [README.md](file:///home/rtroiano/repositories/scripts-public/docs/ai_scoper_dev/README.md) index file linking all 6 markdown files, and verified that navigating to `http://localhost:5070/api/docs/walkthrough` and other documents dynamically renders them inside the browser.
