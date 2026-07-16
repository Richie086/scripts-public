---
name: jira-attachments
description: Automatically tracks, packages, and uploads generated assets (scripts, rules, logs, skills) to a target Jira issue. Use this skill when you need to attach files to the Jira issue you are working on.
---

# Jira Attachments Uploader Skill

This skill enables the agent to automatically track generated files, scripts, logs, and rules, and upload them directly to the active Jira issue using the workspace's attachments uploader script.

## Core Uploader Tool
The primary tool to execute the uploads is:
`/home/rtroiano/repositories/scripts/python/upload_attachments.py`

## Instructions
1. Ensure the Atlassian credentials (`JIRA_URL`, `JIRA_USER`, and `JIRA_API_TOKEN`) are set in the environment or loading via `.env`.
2. Locate the active Jira issue key (e.g. `ATC-67`).
3. Run the uploader script:
   ```bash
   python3 /home/rtroiano/repositories/scripts/python/upload_attachments.py
   ```
4. If you need to attach arbitrary files, use the following Python API pattern:
   ```python
   import requests
   from requests.auth import HTTPBasicAuth

   url = f"{jira_url}/rest/api/3/issue/{issue_key}/attachments"
   auth = HTTPBasicAuth(email, token)
   headers = {
       "X-Atlassian-Token": "no-check",
       "Accept": "application/json"
   }
   with open(filepath, "rb") as f:
       files = {"file": (filename, f)}
       res = requests.post(url, auth=auth, headers=headers, files=files)
   ```

## Best Practices
- **X-Atlassian-Token Header**: Always specify `"X-Atlassian-Token": "no-check"` to bypass CSRF validation.
- **Binary Mode**: Always open files using mode `"rb"` for uploads.
- **Collision Avoidance**: Prepend `skill-` to skill file names (e.g. `skill-<name>-SKILL.md`) to avoid name collisions on the ticket when uploading multiple `SKILL.md` files.
