# Google Antigravity: The AI-First Development Platform You Need to Try

**Google Antigravity** is a powerful, AI-first development platform designed to seamlessly integrate autonomous agentic workflows directly into your coding environment. Whether you are creating a new codebase, modifying an existing one, or just looking to automate repetitive tasks, Antigravity provides the tools you need to build faster and smarter.

In this post, we’ll explore what Google Antigravity is, how to install it, the differences between its IDE and CLI interfaces, basic setup options, and how to configure global agent skills to ensure your generated scripts are secure, complete, and fully functional.

---

## How to Install Google Antigravity via CLI (Mac, Windows, Linux)

Installing Google Antigravity is straightforward across all major operating systems. The easiest way to get started and programmatically access the agent runtime is by installing the Antigravity Python SDK using `pip`. 

Open your terminal and run the following command:

```bash
pip install google-antigravity
```

> **Note:** The SDK relies on a compiled runtime binary included in the platform-specific wheels published to PyPI. Always install using `pip` to ensure you get the correct binary for your OS.

Once installed, you can launch the Antigravity CLI by simply typing:

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

## Configuring Global Agent Skills for Secure, Working Scripts

One of Antigravity's most powerful features is the ability to customize agent behavior using **Skills** and **Rules**. To ensure that your agents consistently produce secure, complete, and working scripts, you should configure your global customizations.

### Step 1: Create a Global Skill
Skills are directories containing specialized instructions that extend the agent's capabilities. Your global customizations root is located at `~/.gemini/config/`.

To create a new skill for secure scripting:
1. Navigate to `~/.gemini/config/skills/` and create a new folder named `secure-scripting`.
2. Inside this folder, create a file named `SKILL.md`.

Add the following content to `SKILL.md`:

```markdown
---
name: secure-scripting
description: Enforces security best practices when writing scripts, ensuring no hardcoded secrets and complete functionality.
---

# Secure Scripting Guidelines
When generating scripts, you MUST adhere to the following rules:
1. **No Hardcoded Secrets:** Never hardcode passwords, API keys, private keys, or usernames. Always use environment variables or prompt the user for input.
2. **Complete Functionality:** Provide fully functional, complete scripts rather than snippets or placeholders.
3. **Error Handling:** Include robust error handling and logging to ensure the script fails gracefully.
```

### Step 2: Define Global Rules
For broader constraints that should apply universally across all tasks and workspaces, you can append rules to your global `AGENTS.md` file.

Open or create `~/.gemini/config/AGENTS.md` and add your security constraints:

```markdown
# Global Agent Rules

## Security Verification (Critical)
- Before executing or proposing any script, verify that it does not contain sensitive data.
- If you detect any potential secrets in the diff, you **must halt** and warn the user explicitly.

## Code Quality
- Ensure all generated code is token-efficient and adheres to modern best practices.
- Do not use command aliases in PowerShell/Bash scripts (e.g., use `Select-Object` instead of `select`) to maintain readability.
```

By setting up these skills and rules, your Antigravity agents will automatically inherit these behaviors, ensuring that the scripts they produce are consistently reliable, secure, and ready for production.

---

**Ready to start building?** Install Google Antigravity today and experience the future of AI-assisted development!
