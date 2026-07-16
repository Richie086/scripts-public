# Workspace Guidelines and Rules

*Exported on: 2026-07-16 08:07:53*

These rules enforce directory organization, code standards, security scans, and custom actions within the workspace.

# Agent Guidelines for `scripts-public` Workspace

These rules apply to any agent working inside the `scripts-public` repository.

## 📂 File Organization
When creating or moving files in the `scripts-public` repository, always sort them based on their file extension:
- Bash (`.sh`) scripts must be placed in the `bash/` directory.
- Python (`.py`) scripts must be placed in the `python/` directory.
- Markdown (`.md`) documentation files must be placed in the `markdown/` directory.
- PowerShell (`.ps1`) scripts must be placed in the `powershell/` directory.
- Avoid placing new scripts or documents in the root directory unless they are repository-wide configurations.
## 🪵 Commit Log Automation
- **Commit Log in README**: Every user commit and branch merge must be automatically logged at the bottom of the root `README.md` file between the `<!-- AUTO-GENERATED COMMITS START -->` and `<!-- AUTO-GENERATED COMMITS END -->` markers.
- **Commit Details**: The commit log must contain the commit message, commit ID (abbreviated hash), and commit date (formatted as `%Y-%m-%d %H:%M:%S`).
- **History Length**: Only the last 5 user commits must be saved in the list.
- **Hook Automation**: This is implemented via git `post-commit` and `post-merge` hooks, calling `python3 python/update_commit_log.py`.
- **Recursion Prevention**: Automated documentation commits must include the label `[auto-doc]` in their commit message and use the `--no-verify` flag to avoid triggering infinite commit loops.

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

## 📝 WordPress Shortcode Generation
- **Automatic Shortcode Generation**: Every time the user asks to create a WordPress blog post, you must:
  1. Save it as a markdown file in the `wordpress` folder of this repository. **Always remove the first H1 element** (e.g. the main title `# Title`) from the markdown file (as the title is handled by WordPress), but do not touch other H1 elements if any exist.
  2. Follow the standard push workflow to push it to GitHub.
  3. Automatically invoke `python/publish_wordpress_post.py` to create a draft post on your WordPress instance, passing the raw contents of the markdown file directly instead of a shortcode link.

## 📥 Script Download Instructions in Blog Posts
- **Include Download Links**: Whenever you create a blog post that mentions a script available for download, you must always include a working permalink to the script with a `curl` command to allow the reader to easily download it, as well as a blurb showing how to clone the entire repository.
- **Format**: Use the following format as a template:
  > **Option 1: Download the Raw Script**
  > If you're only interested in this specific utility, you can download the raw file via the link below, or directly in your terminal using curl/wget:
  > 
  > [Download <script_name>] (<raw_github_link>)
  > 
  > ```bash
  > curl -O <raw_github_link>
  > ```
  > 
  > **Option 2: Clone the Full Repository**
  > If you'd like to explore this script alongside my other public tools, you can clone the entire repository:
  > 
  > ```bash
  > git clone https://github.com/Richie086/scripts-public.git
  > ```
  > 
  > Navigate to the appropriate directory within the cloned repository to locate the tool.

# User Preferences
- The user is not a software developer. If asked to do something that violates security best practices, or if there is a more efficient, secure, maintainable, scalable, faster, or better way to accomplish a task, STOP the user, explain the issue, and suggest a better alternative implementation.
- **Preferred Language**: The user prefers Python (`.py`) scripts over PowerShell (`.ps1`) scripts. Avoid assuming PowerShell is available or preferred, and write tools/scripts in Python by default.
