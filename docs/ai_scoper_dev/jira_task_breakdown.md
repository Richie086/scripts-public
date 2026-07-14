# Jira Task Backlog: AI Jira Scoper & Task Generator

Below is the structured backlog of Epics, Tasks, and Subtasks compiled to complete the remaining gaps (document uploads, git committing, pdf/docx exporting, tuning histories, and containerized deployment configuration).

---

# Epic: Document Ingestion and Server-Side Parsing
Labels: backend, parsing, file-upload
Description: Enable backend ingestion and parsing for binary document formats (PDF, DOCX) and structured file formats (CSV, XML, MD) instead of client-side file reading, and integrate it with the universal dropzone.

## Task: Implement File Upload and Ingestion Endpoint
Labels: backend, api, upload
Description: Create a POST endpoint `/api/parse` in `server.js` that receives multi-part/form-data file uploads and uses the existing `DocumentParser` to extract clean text or returns image details.

### Subtask: Add `multer` middleware to Express server to handle incoming file uploads
Labels: backend, npm
Description: Install `multer` and configure it in `server.js` to process temporary file uploads.

### Subtask: Update `server.js` to route uploaded files to `DocumentParser.parseFile`
Labels: backend, integration
Description: Connect the upload endpoint to `DocumentParser`'s static methods for file extraction.

### Subtask: Create error handling and status responses for unsupported binary formats
Labels: backend, error-handling
Description: Implement catch blocks that identify extraction errors and send appropriate HTTP 400 or 500 error responses to the frontend.

## Task: Connect Frontend Universal Dropzone to Server-Side Parser
Labels: frontend, integration, ajax
Description: Refactor frontend dropzone in `public/app.js` to upload binary files (PDF, DOCX) to the server instead of calling browser `FileReader.readAsText`.

### Subtask: Update `handleFiles` to upload PDF/DOCX files as FormData to `/api/parse`
Labels: frontend, javascript
Description: Modify file handler logic to skip `FileReader` for binary files and make an AJAX request sending the file to the backend parser.

### Subtask: Handle parsed text response and append it to the concept editor textarea
Labels: frontend, UX
Description: Take the parsed text response from the API and append it to `conceptTextarea.value` with clear markdown markers.

### Subtask: Add loading spinner or progress indicators during document upload and parsing
Labels: frontend, UI
Description: Toggle a CSS loading indicator on the universal dropzone element while the parser API call is in progress.

## Task: Improve Document Parser Unit Testing
Labels: testing, backend, QA
Description: Build Jest tests for `DocumentParser` to verify text extraction across all supported formats (PDF, DOCX, CSV, XML, TXT).

### Subtask: Create test fixtures for DOCX, PDF, and CSV files in `tests/fixtures/`
Labels: testing, documentation
Description: Check in mock files containing known content to serve as static test inputs.

### Subtask: Add unit tests verifying `DocumentParser.parseDocx` extracts plain text
Labels: testing, docx
Description: Write Jest asserts matching Mammoth raw text extraction against the DOCX fixture.

### Subtask: Add unit tests verifying `DocumentParser.parsePdf` extracts plain text
Labels: testing, pdf
Description: Write Jest asserts matching `pdf-parse` text extraction against the PDF fixture.

---

# Epic: Git-Driven Change Control & Diff Integration
Labels: backend, frontend, git, change-control
Description: Build a fully interactive change control system that shows a side-by-side comparison (Before vs After) of changes, and writes accepted updates to the codebase on the local `dev` branch.

## Task: Create Change Control Endpoints
Labels: backend, api, git
Description: Implement backend endpoints to track, diff, and write modifications to files, and run Git commands.

### Subtask: Create `/api/git/commit` endpoint to stage and commit specific accepted files
Labels: backend, git
Description: Implement endpoint that runs `git add <file>` and `git commit -m <message>` in the project working directory.

### Subtask: Implement a file-writing endpoint (`POST /api/git/write`) to write accepted changes
Labels: backend, fs
Description: Create endpoint to write final accepted text payload to target workspace files (e.g., code files or spec markdown).

### Subtask: Implement a simple diff comparison utility or interface to return line-by-line diffs
Labels: backend, algorithm
Description: Create backend logic to compare original file content with proposed modifications and output structured diffs (added/removed lines).

## Task: Implement Before-and-After Diff Pane UI
Labels: frontend, UI, design
Description: Design and implement a side-by-side comparison container (Before vs After) in `tab-expand` and `tab-prompt` to display proposed modifications before they are committed.

### Subtask: Build CSS styling for side-by-side layout matching the active developer color theme
Labels: frontend, css
Description: Setup layout styles with beveled borders and glassmorphism styling for Dracula, Nord, Gruvbox, One Dark, and Solarized Dark themes.

### Subtask: Write frontend JavaScript to populate "Before" and "After" panels
Labels: frontend, javascript
Description: Fetch current file contents for the "Before" pane and generated outputs for the "After" pane when changes are generated.

### Subtask: Create line-by-line diff highlighting (green for additions, red for deletions)
Labels: frontend, css
Description: Highlight added and deleted lines using theme-specific variables (e.g., `--accent-green`, `--accent-red`).

## Task: Support Full Interactive Lifecycle Control
Labels: frontend, UX, integration
Description: Connect the Accept, Edit, Discard, and Regenerate buttons to backend actions and update workspace states.

### Subtask: Hook up "Accept" button to write to workspace files and commit them to the `dev` branch
Labels: frontend, javascript
Description: Call `POST /api/git/write` and `POST /api/git/commit` sequentially, then show a success toast.

### Subtask: Hook up "Edit" button to toggle a raw text editor (`textarea`) over the proposed change pane
Labels: frontend, UI
Description: Swap the rendered diff pane for an editable textarea allowing manual tuning before accept/commit.

### Subtask: Hook up "Discard" button to close the diff pane and restore original workspace state
Labels: frontend, UX
Description: Clean up temporary changes and close the panel without committing.

### Subtask: Hook up "Regenerate" button to re-invoke the LLM with a variation prompt
Labels: frontend, llm
Description: Re-trigger LLM concept expansion with additional user prompt feedback input.

---

# Epic: Multi-Format Exporter Expansion
Labels: backend, export, document-generation
Description: Extend the exporter engine to handle document generation for `.docx` and `.pdf` formats, and ensure clean structure for the Jira CSV import files.

## Task: Implement PDF Document Exporter
Labels: backend, api, pdf
Description: Implement PDF exporting in `/api/export` using a library like `pdfkit` or `html-pdf` to generate styled reports.

### Subtask: Install and configure `pdfkit` in `package.json`
Labels: backend, npm
Description: Add dependency for PDF generation and install packages.

### Subtask: Write a helper module to format markdown text into a styled PDF document
Labels: backend, utils
Description: Format sections, code blocks (using JetBrains Mono layout), tables, and titles to look professional.

### Subtask: Connect `/api/export` PDF request type to the generator
Labels: backend, api
Description: Handle the PDF download request type and pipe the output stream back to the response.

## Task: Implement Word DOCX Document Exporter
Labels: backend, api, docx
Description: Implement Word Document (.docx) exporting in `/api/export` using a library like `docx` to generate cleanly formatted documents.

### Subtask: Install and configure `docx` or similar library
Labels: backend, npm
Description: Add dependency to `package.json` and initialize it in the exporter service.

### Subtask: Format section headers, lists, and tables to render neatly in Microsoft Word
Labels: backend, utils
Description: Map markdown structures into DOCX document components (Paragraphs, Tables, TableRows, TableCells).

### Subtask: Connect `/api/export` Word request type to send the generated buffer
Labels: backend, api
Description: Stream the docx buffer back to the client with correct headers (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`).

## Task: Refine Jira CSV Exporter for Parent-Child Hierarchies
Labels: backend, csv
Description: Refine the CSV output logic in `server.js` to ensure the generated file cleanly maps the `Issue ID`, `Summary`, `Description`, `Issue Type`, `Parent ID`, and `Labels` fields for a nested hierarchy.

### Subtask: Fix regex parsing of generated Markdown text to extract nested issues correctly
Labels: backend, parsing
Description: Fix edge cases where markdown formatting variations break Epic, Story, and Subtask extraction regexes.

### Subtask: Map Epics, Tasks/Stories, and Sub-tasks to their corresponding Jira IDs
Labels: backend, data-mapping
Description: Ensure proper Parent ID references for Tasks/Stories (child of Epic ID) and Sub-tasks (child of Task ID).

### Subtask: Verify character escaping (e.g., quotes, commas) does not break CSV parsing
Labels: backend, csv
Description: Properly escape double quotes and commas within the summary and description cells to avoid broken CSV grids on Jira import.

---

# Epic: LLM Client & Prompt Tuner Enhancements
Labels: backend, llm, prompt-engineering
Description: Improve provider configuration options (like custom baseURLs and custom headers) and implement conversational prompt tuning history.

## Task: Complete Custom Internal LLM Setup
Labels: backend, llm, security
Description: Extend `LLMClient` to support custom headers and model configurations for local LLMs like Ollama.

### Subtask: Update `llmClient.js` to accept `customHeaders` in the request config
Labels: backend, javascript
Description: Add parser to extract custom authentication or routing headers from the request payload.

### Subtask: Verify internal client properly forwards API keys/authorization headers to base URLs
Labels: backend, axios
Description: Test proxy calls with custom authorization bearer headers.

### Subtask: Add a UI section in the sidebar for adding custom request headers (JSON format)
Labels: frontend, UI
Description: Add a JSON-validated textarea in the sidebar configuration drawer for custom HTTP headers.

## Task: Build Conversational Tuning History
Labels: frontend, backend, chat
Description: Implement message history tracking in the Prompt Tuner chat interface so the AI remembers previous prompt edits.

### Subtask: Add a state variable to store chat history (`messages` array) in the frontend
Labels: frontend, state
Description: Store ongoing dialogue history in `public/app.js` to keep track of user tuning statements.

### Subtask: Update `/api/prompt/tune` endpoint to accept a message history array
Labels: backend, api
Description: Rewrite endpoint handler to receive the full chat history instead of a single statement.

### Subtask: Modify the LLM prompt generator to include the conversation context for refinements
Labels: backend, prompt-engineering
Description: Format the chat history cleanly into the system instructions for continuous prompt modifications.

## Task: Create Master Prompt Template Artifact
Labels: documentation, artifact
Description: Create the `master_prompt_template.md` file containing detailed system instructions instructing an LLM on how to build and validate this entire application from scratch.

### Subtask: Draft standard instructions for building the Express backend and single-page frontend
Labels: prompt-engineering
Description: Detail the server.js routing structure and styling rules for the application.

### Subtask: Include instructions for file dropzone, security scanning regexes, code compilers, and Jira CSV exports
Labels: prompt-engineering
Description: Detail regex patterns for PII, mammoth/pdf-parse integrations, compile commands for Javascript/Python, and CSV hierarchy formats.

### Subtask: Commit `master_prompt_template.md` under the root project directory
Labels: documentation, git
Description: Write the compiled master prompt to the codebase.

---

# Epic: Verification & DevOps Deployment
Labels: devops, testing, deployment
Description: Construct full automated test suites, setup CI, and establish the local deployment strategy for the application.

## Task: Create Full Backend Integration Test Suite
Labels: testing, backend, QA
Description: Build integration tests using `supertest` for all `/api` endpoints in `server.js`.

### Subtask: Create `tests/server.test.js` to test `/api/scan`, `/api/expand`, `/api/syntax/check`, and `/api/export` routes
Labels: testing, supertest
Description: Set up API tests utilizing `supertest` to verify status codes and responses.

### Subtask: Mock the LLM client in the test suite to prevent API charges and ensure deterministic outputs
Labels: testing, mocks
Description: Mock `llmClient.js` behaviors for all Jest integration test scenarios.

### Subtask: Verify correct HTTP status codes and payloads for valid and invalid inputs
Labels: testing, validations
Description: Check error states, bad configurations, empty concept uploads, and boundary cases.

## Task: Build Syntax Validator Test Suite
Labels: testing, syntax-checker
Description: Write automated tests to verify the compiler-based syntax validation for Python and JavaScript code snippets.

### Subtask: Create test files with valid/invalid JavaScript syntax and run them through `/api/syntax/check`
Labels: testing, javascript
Description: Assert success on valid JS syntax, and assert correct error structure on syntax-broken files.

### Subtask: Create test files with valid/invalid Python syntax and run them through the checker
Labels: testing, python
Description: Assert success on valid Python syntax, and check syntax compilation warnings on syntax-broken files.

### Subtask: Test error output formatting to ensure line numbers and details are returned clearly to the UI
Labels: testing, UI-integrity
Description: Assert error messages return lines numbers and compiler-specific errors rather than generic HTTP failure notices.

## Task: Local Deployment & Daemon Setup
Labels: devops, deployment, containerization
Description: Create configuration scripts to run the application locally as a background daemon.

### Subtask: Create a `docker-compose.yml` file to containerize the Node.js application
Labels: devops, docker
Description: Define container rules, bind mounting of local repository, and environment configuration mappings.

### Subtask: Write a systemd service file `ai-scoper.service` to daemonize the process
Labels: devops, linux
Description: Set up a local user-scoped systemd script that spins up the web server on boot.

### Subtask: Document setup instructions in a README.md file
Labels: documentation
Description: Create a clear user guide outlining installation steps, configuration settings, docker-compose start parameters, and port usage.
