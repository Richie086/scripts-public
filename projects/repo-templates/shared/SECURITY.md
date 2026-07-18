# Security & sensitive data

- Never commit real secrets, credentials, or PII. Use `.env` (gitignored) and commit only `.env.example` with placeholder values.
- This repo is scanned by [gitleaks](https://github.com/gitleaks/gitleaks) on every commit (pre-commit hook) and every push (CI workflow `secret-scan.yml`), using the shared `.gitleaks.toml` config.
- If a scan flags a false positive (test fixture, example data), add a narrow entry to the `[allowlist]` section of `.gitleaks.toml` rather than disabling the hook.
- If a real secret is ever committed: rotate it immediately, then scrub history (`git filter-repo` or BFG) — removing the file in a later commit is not enough.
