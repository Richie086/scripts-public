---
name: suggest-skills
description: |
  Automatically suggests new custom skills to add functionality to IgniteAi by analyzing current backlogs, user instructions, and external API documentation.
---

# IgniteAi Skill Suggester

This skill analyzes current automation tasks, project rules, and codebase setups to identify gaps and suggest new modular skills that can extend IgniteAi's capabilities.

## Usage

1. **Analyze Backlog**: Inspect your active backlogs (e.g. Jira tasks, confluence pages, or repository scripts) to identify repetitive patterns or manual processes.
2. **Suggest Skills**: Propose a structured description of potential new skills to the user, including:
   - **Name**: Short kebab-case identifier (e.g., `github-actions-automation`).
   - **Description**: Summary of the new skill.
   - **Prerequisites & API Targets**: The tools, credentials, or environments required.
   - **Implementation Path**: Folder location and script structures.

## Example Suggestions
- **github-issue-sync**: Integrates with GitHub CLI to sync backlog issues from GitHub to Jira automatically.
- **bitbucket-pipeline-monitor**: Regularly scans Bitbucket Cloud pipeline execution states and reports failures to Jira task updates.
