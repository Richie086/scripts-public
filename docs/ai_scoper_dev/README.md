# Table of Contents: AI Jira Scoper & Task Generator Documentation

This document serves as a central index linking all generated design plans, backlogs, tutorials, and validation reports for the **AI Jira Scoper & Task Generator** application.

---

## 1. Documentation Index

The following specifications are versioned inside the public repository:

| Document Title | Description | Local / GitHub File Link | Browser Render Link |
|---|---|---|---|
| **1. Implementation Plan** | Full system design, UI features, and verification checklist. | [ai_scoper_app_plan.md](./ai_scoper_app_plan.md) | [http://localhost:5070/api/docs/ai_scoper_app_plan](http://localhost:5070/api/docs/ai_scoper_app_plan) |
| **2. Atlassian Plugin Plan** | System architecture for hybrid Jira/Bitbucket/Confluence integration plugin. | [jira_ai_plugin_plan.md](./jira_ai_plugin_plan.md) | [http://localhost:5070/api/docs/jira_ai_plugin_plan](http://localhost:5070/api/docs/jira_ai_plugin_plan) |
| **3. Jira Task Backlog** | Epic, Story, and Subtask task breakdown for project execution. | [jira_task_breakdown.md](./jira_task_breakdown.md) | [http://localhost:5070/api/docs/jira_task_breakdown](http://localhost:5070/api/docs/jira_task_breakdown) |
| **4. Jira API Token Guide** | Tutorial on generating secure credentials for script authentication. | [jira_token_guide.md](./jira_token_guide.md) | [http://localhost:5070/api/docs/jira_token_guide](http://localhost:5070/api/docs/jira_token_guide) |
| **5. Master Prompt Template** | Single-file blueprint prompt to replicate the entire workspace build. | [master_prompt_template.md](./master_prompt_template.md) | [http://localhost:5070/api/docs/master_prompt_template](http://localhost:5070/api/docs/master_prompt_template) |
| **6. Walkthrough & Verification** | Log of automated Jest test suites and manual REST endpoint validations. | [walkthrough.md](./walkthrough.md) | [http://localhost:5070/api/docs/walkthrough](http://localhost:5070/api/docs/walkthrough) |

---

## 2. Dynamic Documentation Server
The Express server has been updated with a generic documentation rendering endpoint. While the server is running on port `5070`, you can append any document filename in the URL to render it as styled HTML:
* Format: `http://localhost:5070/api/docs/<filename>`
* Examples:
  - [http://localhost:5070/api/docs/walkthrough](http://localhost:5070/api/docs/walkthrough)
  - [http://localhost:5070/api/docs/jira_task_breakdown](http://localhost:5070/api/docs/jira_task_breakdown)
