---
name: jira-uploader
description: |
  Automates parsing a structured markdown backlog file (Epics, Tasks, and Subtasks) and uploading them to a Jira Cloud instance using the upload_jira_tasks.py script.
---

# Jira Backlog Uploader

This skill allows the agent to parse a structured markdown backlog file and provision projects, Epics, Tasks, and Subtasks programmatically in a Jira Cloud instance.

## Prerequisites

Before running the uploader, ensure you have the following credentials:
- **JIRA_URL**: The base URL of your Jira Cloud instance (e.g., `https://your-domain.atlassian.net`).
- **JIRA_USER**: The email address of the Jira user/administrator.
- **JIRA_API_TOKEN**: The Atlassian API Token generated from your security settings.

## Backlog Format

The source markdown file should follow this structure:
- **Epic**: Denoted by `# Epic: <Epic Title>`
- **Task**: Denoted by `## Task: <Task Title>`
- **Subtask**: Denoted by `### Subtask: <Subtask Title>`
- **Labels**: Denoted by `Labels: label1, label2`
- **Description**: Standard markdown text or paragraphs underneath the header and labels.

## Instructions

1. **Dry-Run Check**:
   First, validate the markdown parsing logic and backlog hierarchy by executing a dry-run:
   ```bash
   python3 /home/rtroiano/repositories/scripts/python/upload_jira_tasks.py --path <path_to_backlog_markdown> --dry-run
   ```
   Verify the output correctly lists all Epics, Tasks, and Subtasks.

2. **Upload Backlog**:
   Execute the uploader script with the required credentials passed via environment variables:
   ```bash
   JIRA_URL="<JIRA_URL>" \
   JIRA_USER="<JIRA_USER>" \
   JIRA_API_TOKEN="<JIRA_API_TOKEN>" \
   python3 /home/rtroiano/repositories/scripts/python/upload_jira_tasks.py \
       --path <path_to_backlog_markdown> \
       --project-key <PROJECT_KEY> \
       --project-name "<PROJECT_NAME>"
   ```
   *Note: If the primary `Subtask` creation fails on certain Classic configurations, the script automatically attempts a fallback to `Sub-task` issue types.*
