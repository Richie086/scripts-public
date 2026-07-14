# Table of Contents: AI Jira Scoper & Task Generator Documentation

This document serves as a central index linking all generated design plans, backlogs, tutorials, and validation reports for the **AI Jira Scoper & Task Generator** application.

---

## 1. Documentation Index

The following specifications are versioned inside the public repository:

| Document Title | Description | Local File Link | Browser Render Link | GitHub Repository Link |
|---|---|---|---|---|
| **1. Implementation Plan** | Full system design, UI features, and verification checklist. | [ai_scoper_app_plan.md](file:///home/rtroiano/repositories/scripts-public/docs/ai_scoper_dev/ai_scoper_app_plan.md) | [http://localhost:5070/api/docs/ai_scoper_app_plan](http://localhost:5070/api/docs/ai_scoper_app_plan) | [GitHub Link](https://github.com/Richie086/scripts-public/blob/master/docs/ai_scoper_dev/ai_scoper_app_plan.md) |
| **2. Atlassian Plugin Plan** | System architecture for hybrid Jira/Bitbucket/Confluence integration plugin. | [jira_ai_plugin_plan.md](file:///home/rtroiano/repositories/scripts-public/docs/ai_scoper_dev/jira_ai_plugin_plan.md) | [http://localhost:5070/api/docs/jira_ai_plugin_plan](http://localhost:5070/api/docs/jira_ai_plugin_plan) | [GitHub Link](https://github.com/Richie086/scripts-public/blob/master/docs/ai_scoper_dev/jira_ai_plugin_plan.md) |
| **3. Jira Task Backlog** | Epic, Story, and Subtask task breakdown for project execution. | [jira_task_breakdown.md](file:///home/rtroiano/repositories/scripts-public/docs/ai_scoper_dev/jira_task_breakdown.md) | [http://localhost:5070/api/docs/jira_task_breakdown](http://localhost:5070/api/docs/jira_task_breakdown) | [GitHub Link](https://github.com/Richie086/scripts-public/blob/master/docs/ai_scoper_dev/jira_task_breakdown.md) |
| **4. Jira API Token Guide** | Tutorial on generating secure credentials for script authentication. | [jira_token_guide.md](file:///home/rtroiano/repositories/scripts-public/docs/ai_scoper_dev/jira_token_guide.md) | [http://localhost:5070/api/docs/jira_token_guide](http://localhost:5070/api/docs/jira_token_guide) | [GitHub Link](https://github.com/Richie086/scripts-public/blob/master/docs/ai_scoper_dev/jira_token_guide.md) |
| **5. Master Prompt Template** | Single-file blueprint prompt to replicate the entire workspace build. | [master_prompt_template.md](file:///home/rtroiano/repositories/scripts-public/docs/ai_scoper_dev/master_prompt_template.md) | [http://localhost:5070/api/docs/master_prompt_template](http://localhost:5070/api/docs/master_prompt_template) | [GitHub Link](https://github.com/Richie086/scripts-public/blob/master/docs/ai_scoper_dev/master_prompt_template.md) |
| **6. Walkthrough & Validation** | Log of automated Jest test suites and manual REST endpoint validations. | [walkthrough.md](file:///home/rtroiano/repositories/scripts-public/docs/ai_scoper_dev/walkthrough.md) | [http://localhost:5070/api/docs/walkthrough](http://localhost:5070/api/docs/walkthrough) | [GitHub Link](https://github.com/Richie086/scripts-public/blob/master/docs/ai_scoper_dev/walkthrough.md) |

---

## 2. Dynamic Documentation Server
The Express server has been updated with a generic documentation rendering endpoint. While the server is running on port `5070`, you can append any document filename in the URL to render it as styled HTML:
* Format: `http://localhost:5070/api/docs/<filename>`
* Examples:
  - [http://localhost:5070/api/docs/walkthrough](http://localhost:5070/api/docs/walkthrough)
  - [http://localhost:5070/api/docs/jira_task_breakdown](http://localhost:5070/api/docs/jira_task_breakdown)
