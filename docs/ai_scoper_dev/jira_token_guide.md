# Guide: Creating an Atlassian Jira Cloud API Token

Follow these steps to generate a secure API Token for authenticating scripts and applications against your Atlassian Jira Cloud instance.

---

### Step 1: Navigate to Atlassian Security Settings
1. Open your web browser and go to your Atlassian Profile Security center:
   👉 **[https://id.atlassian.com/manage-profile/security](https://id.atlassian.com/manage-profile/security)**
2. Log in using your Atlassian credentials if prompted.

### Step 2: Access API Token Management
1. Scroll down to the **API Token** section on the page.
2. Click the link labeled **Create and manage API tokens**.

### Step 3: Create a New Token
1. Click the blue **Create API token** button at the top of the list.
2. In the modal that appears, enter a descriptive label for your token (e.g., `AutoTask-Ai-Generator` or `Jira-Backlog-Uploader`).
3. Click **Create**.

### Step 4: Copy & Save the Token
1. A popup window will display your newly generated API Token.
2. Click **Copy** to copy the token to your clipboard.
3. > [!CAUTION]
   > Save the copied token immediately to a password manager or secure location. Atlassian will not show this token again once you close this window.
4. Click **Close**.

---

### Step 5: Using the Token in Terminal
In your terminal, authenticate the uploader script by setting the token as an environment variable:

```bash
export JIRA_URL="https://your-company.atlassian.net"
export JIRA_USER="your-email@example.com"
export JIRA_API_TOKEN="paste_your_copied_api_token_here"
```
Once set, you can securely execute the script:
```bash
python3 python/upload_jira_tasks.py
```
