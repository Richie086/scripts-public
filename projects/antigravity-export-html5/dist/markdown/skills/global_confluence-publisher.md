---
name: confluence-publisher
description: |
  Automates the process of generating and publishing structured project dashboards, issue trackers, and technical analysis reports to Confluence Cloud using the create_confluence_page.py and post_analysis_to_confluence.py scripts.
---

# Confluence Page Publishing Automation

This skill guides the agent through querying Jira issues, formatting the data into Confluence-compatible XHTML storage format, embedding live Jira Issue Macros, and publishing pages to Confluence Cloud.

## Prerequisites

Ensure the following credentials are set in the execution environment:
- **JIRA_URL**: The base URL of the Atlassian instance (e.g., `https://your-domain.atlassian.net`).
- **JIRA_USER**: The email address of the Atlassian user.
- **JIRA_API_TOKEN**: The Atlassian API Token generated from your security settings.

## Instructions

1. **Jira Issue Backlog Tracker**:
   To generate a live-updating backlog status page linking to all Jira issues in project `ATC`, run:
   ```bash
   JIRA_URL="<JIRA_URL>" \
   JIRA_USER="<JIRA_USER>" \
   JIRA_API_TOKEN="<JIRA_API_TOKEN>" \
   python3 /home/rtroiano/repositories/scripts/python/create_confluence_page.py
   ```
   *Note: This script automatically groups issues by Epic/Task/Subtask hierarchy and embeds the live `<ac:structured-macro ac:name="jira">` macro for real-time status badges.*

2. **Custom Issue Type Analysis Report**:
   To publish the technical analysis report detailing the custom Jira issue types mapping and manual configuration steps, run:
   ```bash
   JIRA_URL="<JIRA_URL>" \
   JIRA_USER="<JIRA_USER>" \
   JIRA_API_TOKEN="<JIRA_API_TOKEN>" \
   python3 /home/rtroiano/repositories/scripts/python/post_analysis_to_confluence.py
   ```

## Script & Skill File References
- **Backlog Page Creator**: `/home/rtroiano/repositories/scripts/python/create_confluence_page.py`
- **Analysis Page Creator**: `/home/rtroiano/repositories/scripts/python/post_analysis_to_confluence.py`
- **Skill Directory**: `/home/rtroiano/.gemini/skills/confluence-publisher`
