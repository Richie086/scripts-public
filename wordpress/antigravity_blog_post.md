**Google Antigravity** is a powerful, AI-first development platform designed to seamlessly integrate autonomous agentic workflows directly into your coding environment. Whether you are creating a new codebase, modifying an existing one, or just looking to automate repetitive tasks, Antigravity provides the tools you need to build faster and smarter.

In this post, we’ll explore what Google Antigravity is, how to install it, the differences between its IDE and CLI interfaces, basic setup options, and how to configure global agent skills to ensure your generated scripts are secure, complete, and fully functional.

---

## How to Install Google Antigravity (Mac, Windows, Linux)

Google Antigravity is available as both a Desktop Application (Antigravity 2.0) and a CLI/Python SDK. Here is how to install the platform on your operating system of choice.

### 1. Installing the Desktop Application (Antigravity 2.0)
If you prefer a full graphical interface, you can download the standalone desktop application for your OS directly from the official site:
* 🪟 **Windows:** [Download for Windows](https://antigravity.google/download/windows)
* 🍎 **macOS:** [Download for macOS](https://antigravity.google/download/macos) (Apple Silicon & Intel)
* 🐧 **Linux:** [Download for Linux](https://antigravity.google/download/linux) (.deb and AppImage available)

Once downloaded, run the installer, launch the app, and follow the on-screen prompts to authenticate with your Google account.

### 2. Installing the CLI & Python SDK
For developers who want to stay in the terminal or programmatically access the agent runtime, you can install the Antigravity Python SDK using `pip`. This works universally across Mac, Windows, and Linux.

Open your terminal and run:

```bash
pip install google-antigravity
```

> **Note:** The SDK relies on a compiled runtime binary included in the platform-specific wheels published to PyPI. Always install using `pip` to ensure you get the correct binary for your OS architecture.

Once installed, you can launch the Antigravity CLI by typing:

```bash
agy
```

On your first run, the CLI will prompt you to press `Enter` to open a browser window for Google OAuth authentication. Once authenticated, paste the provided code back into your terminal, and you are ready to go!

---

## Exploring the Interfaces: IDE vs. CLI

Google Antigravity provides distinct interfaces tailored to how you prefer to work.

### 1. Antigravity IDE
The Antigravity IDE is a standalone, AI-first integrated development environment (built on VS Code). It offers three core interaction modalities:

*   **Passive (Autocomplete):** A next-intent prediction experience that proposes insertions, deletions, and cursor movements based on your surrounding code and open tabs.
*   **Instructive (Inline Commands):** Highlight a block of code and press `Cmd+I` (Mac) or `Ctrl+I` (Windows/Linux) to ask the AI to refactor, explain, or modify that specific block. 
*   **Collaborative (Sidebar Chat & Agent):** The primary panel for complex tasks. Launch an agent that can act as a multi-step pair programmer—capable of reading and writing files, running terminal commands, searching the web, and executing tools autonomously.

### 2. Antigravity CLI (`agy`)
For developers who prefer staying in the terminal, the Antigravity CLI (`agy`) offers a lightweight, interactive Terminal User Interface (TUI). 

With the CLI, you can use built-in slash commands to manage your workspace and interact with agents. Some useful commands include:
*   `/config` or `/settings`: Open the TUI configuration panel.
*   `/diff`: View the current codebase diff of changes made by the agent.
*   `/skills`: List all active agent skills.
*   `/tasks`: Display the active task list and progress.

---

## Advanced Configuration for SysAdmins & DevOps

Antigravity is highly customizable and built with enterprise security in mind. You can configure your environment using the CLI via the `~/.gemini/antigravity-cli/settings.json` file or through the Settings panel in the Antigravity desktop application. 

For System Administrators and DevOps engineers managing deployments, here are the crucial configuration keys to secure your environment:

*   **`enableTerminalSandbox` (Security):** Set this boolean to `true` to force all agent-executed terminal commands to run inside a restricted sandbox environment, preventing accidental system modifications.
*   **`toolPermission` (Execution Policy):** Controls whether the agent requires explicit approval before running commands. Options include `always-proceed`, `request-review`, `strict`, or `proceed-in-sandbox`. For production environments, `strict` or `request-review` is recommended.
*   **`permissions` (Granular ACLs):** Define explicit allow/deny/ask rules for specific files, terminal commands, and URLs. This is essential for ensuring the agent only interacts with approved CI/CD scripts and safe domains.
*   **`allowNonWorkspaceAccess` (Boundary Control):** Permits or denies the agent's ability to read or write files outside the current workspace root (`true`/`false`).
*   **`trustedWorkspaces` (Trust Zones):** An array of directory paths trusted for execution. You can whitelist specific repositories where agent activity is fully permitted.
*   **`gcp` (Cloud Integration):** An object for GCP project and location configurations, enabling seamless and authenticated interaction with Google Cloud tools and deployments.
*   **`enableTelemetry` (Privacy):** A boolean to toggle anonymous usage and crash reporting based on your organization's data privacy policies.
*   **`model` (Model Selection):** Set the active model identifier (e.g., `gemini-3.5-flash` or `gemini-pro`) to balance speed, cost, and capability.

---

## Configuring Agent Skills and Rules for Secure, Working Scripts

One of Antigravity's most powerful features is the ability to customize agent behavior using **Skills** and **Rules**. You can apply these globally or scope them to specific workspaces (projects).

### 1. Workspace-Scoped Rules (`AGENTS.md`)
To enforce strict behaviors for a specific project, you can create a `.agents` folder in the root of your workspace and add an `AGENTS.md` file. The agent will read this file every time it operates in that workspace.

Here is an example of a robust, real-world `AGENTS.md` configuration used to ensure scripts are fully documented, secure, and properly version-controlled:

```markdown
# Agent Guidelines for `scripts-public` Workspace

## 📝 Documenting Changes
- **Enforce Documentation Updates**: Any changes, additions, or removals of scripts/files in this repository must be reflected and documented in the README.md file.

## 🛡️ Pre-Commit Sensitive Data Verification (Critical)
- **Do Not Disclose Sensitive Data**: Sensitive information like passwords, API keys, private keys, or certificates must **never** be committed.
- **Pre-Commit Scan**: Before staging, committing, or pushing any changes, you **must** scan all files in the current diff for sensitive patterns (e.g., `-----BEGIN PRIVATE KEY-----`, hardcoded passwords, `CERT_PASS`).
- **Warning System**: If you detect any sensitive information in the diff, you **must halt** and warn the user explicitly using a clear warning message:
  > [!CAUTION]
  > **Sensitive Data Detected!** You are about to commit sensitive information. Please verify if you want to proceed.

## 🚀 Git Pushing Workflow (Pre-Push Approval)
- **Automate Local Git Tasks**: When the user requests a push to GitHub, automate all intermediate steps:
  1. Stage files (`git add`).
  2. Run the security scan (`git diff --cached`).
  3. Commit locally with a descriptive commit message (`git commit -m "..."`).
- **Prompt Before Push**: **Stop** before executing the final `git push` command. Prompt the user for explicit confirmation or approval before running `git push`.
```

### 2. Creating Reusable Agent Skills
While rules are great for constraints, **Skills** provide specialized capabilities. A skill is a directory placed in your global `~/.gemini/config/skills/` folder containing a `SKILL.md` file with a YAML frontmatter.

For example, to create a skill that enforces secure script generation across all projects, create `~/.gemini/config/skills/secure-scripting/SKILL.md`:

```markdown
---
name: secure-scripting
description: Enforces security best practices when writing scripts, ensuring no hardcoded secrets and complete functionality.
---

# Secure Scripting Guidelines
When generating scripts, you MUST adhere to the following rules:
1. **No Hardcoded Secrets:** Always use environment variables or prompt the user for input.
2. **Complete Functionality:** Provide fully functional, complete scripts rather than snippets or placeholders.
3. **Error Handling:** Include robust error handling and logging to ensure the script fails gracefully.
```

### 3. Ask Antigravity for Security Enhancements!
Antigravity isn't just a rule-follower—it's an active collaborator. If you aren't sure what other security measures you should put in place, just ask! 

Try sending a prompt like this to the agent:
> *"Review my current workspace configuration and suggest more actions or rules you can perform related to security and DevOps best practices. How else can we lock this down?"*

The agent can analyze your setup and suggest adding specific linting rules, deploying credential scanning tools (like `trufflehog`), or creating new automated background tasks to keep your environment secure.

---

**Ready to start building?** Install Google Antigravity today and experience the future of AI-assisted development!
