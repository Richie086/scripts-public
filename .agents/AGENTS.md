# Agent Guidelines for `scripts-public` Workspace

These rules apply to any agent working inside the `scripts-public` repository.

## 📝 Documenting Changes
- **Enforce Documentation Updates**: Any changes, additions, or removals of scripts/files in this repository must be reflected and documented in the README.md file.
- **Maintain Catalog Alignment**: Ensure the documentation links and structural references remain accurate.

## 🛡️ Pre-Commit Sensitive Data Verification (Critical)
- **Do Not Disclose Sensitive Data**: Sensitive information like passwords, API keys, private/public keys, certificates, or usernames must **never** be added to the README.md or documentation under any circumstances.
- **Pre-Commit Scan**: Before staging, committing, or pushing any changes, you **must** scan all files in the current diff for sensitive patterns, including but not limited to:
  - Private keys (e.g., `-----BEGIN PRIVATE KEY-----`)
  - Passwords or credentials (e.g., hardcoded passwords, `CERT_PASS`, `passwd`)
  - Secret API tokens or keys
  - Active certificates (e.g., `cert.pem`, `key.pem`)
  > [!CAUTION]
  > **Sensitive Data Detected!** You are about to commit sensitive information (passwords, keys, or certificates). Please verify if you want to proceed.

## 🚀 Git Pushing Workflow (Pre-Push Approval)
- **Automate Local Git Tasks**: When the user requests a push to GitHub, automate all intermediate steps:
  1. Stage files (`git add`).
  2. Run the security scan (`git diff --cached`).
  3. Commit locally with a descriptive commit message (`git commit -m "..."`).
- **Prompt Before Push**: **Stop** before executing the final `git push` command. Prompt the user for explicit confirmation or approval before running `git push`.

