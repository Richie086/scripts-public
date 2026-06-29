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
- **Warning System**: If you detect any sensitive information in the diff, you **must halt** and warn the user explicitly before proceeding with any commit or push, using a clear warning message such as:
  > [!CAUTION]
  > **Sensitive Data Detected!** You are about to commit sensitive information (passwords, keys, or certificates). Please verify if you want to proceed.
