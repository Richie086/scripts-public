# Goal

Every script in this repo runs cleanly with any documented CLI option/flag, and every web app is reachable and interactive via a local browser (or remote URL when deployed)—backed by unit tests, flag tests, and help/docs that guide a user through each tool.

# Done when

For each tool the loop picks up (one tool per session):

1. **CLI scripts**
   - `--help` / `-h` (or equivalent) exits 0 and prints usage.
   - Every documented flag/option can be invoked without unhandled errors (invalid combos may exit non-zero with a clear message).
   - Automated tests cover: help output, each major flag path, and at least one happy-path run with safe/mock fixtures where real side effects would be destructive.
   - README (or adjacent docs) matches the real flags and walks a new user through install → first run → common options.

2. **Web apps**
   - App starts locally (documented command) and is reachable in a browser.
   - Core UI is interactive end-to-end (smoke: load page → perform primary action → see expected result).
   - Help/docs describe how to run locally and (if applicable) remotely.

3. **Verification gate**
   - Tool-specific test command is green (prefer `bash`/`python -m pytest` / project test runner as appropriate).
   - `/verify` passes against the session diff before commit.
   - `IMPLEMENTATION_PLAN.md` marks the tool done and lists the next tool (or `STATUS: done` when the inventory is empty).

# Never touch

- `scripts-public/python/` — do not run, harden, test, or document tools in this folder.
- Prefer additive changes (tests, help, docs) over drive-by refactors of unrelated tools in the same session.

# Stop if

- More than one tool is changed in a single session (single-feature rule).
- A previously green test suite for another tool starts failing.
- Destructive live ops (mail, SSH, user delete, KVM provision) are run against real hosts without dry-run/fixtures—use mocks or documented safe modes instead.
- Scope expands into a greenfield product unrelated to making an existing script/app runnable, testable, and documented.
- The session targets anything under `scripts-public/python/`.
